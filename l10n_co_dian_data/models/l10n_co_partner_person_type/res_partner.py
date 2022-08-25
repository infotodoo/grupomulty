# Copyright 2013 Nicolas Bessi (Camptocamp SA)
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, fields, models, _
# from odoo.addons.partner_firstname import exceptions
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from ... import exceptions


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Adds last name and first name; name becomes a stored function field."""

    _inherit = "res.partner"

    firstname = fields.Char("Primer Nombre", index=True)
    lastname = fields.Char("Last name", index=True)
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True,
        readonly=False,)
    lastname2 = fields.Char("Second last name")
    othernames = fields.Char("Other Names")
    person_type = fields.Selection([("1", "Juridical Person and assimilated"),
                                    ("2", "Natural Person and assimilated")], string="Person Type")
    same_identification_document_partner_id = fields.Many2one(
        'res.partner',
        string='Partner with same identification document',
        compute='_compute_same_identification_document_partner_id',
        store=False
    )

    @api.onchange("person_type")
    def onchange_person_type(self):
        if self.person_type == "1":
            self.company_type = "company"
        elif self.person_type == "2":
            self.company_type = "person"

    @api.model
    def _get_computed_name(self, firstname, othernames, lastname, lastname2):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        order = self._get_names_order()
        
        if order == "last_first_comma":
            names = []
            if lastname:
                names.append(lastname)
            if lastname2:
                names.append(lastname2)
            if names and (firstname or othernames):
                names[-1] = names[-1] + ","
            if firstname:
                names.append(firstname)
            if othernames:
                names.append(othernames)
            return " ".join(p for p in names if p)
        elif order == "first_last":
            return " ".join(p for p in (firstname, othernames, lastname, lastname2) if p)
        else:
            return " ".join(p for p in (lastname, lastname2, firstname, othernames) if p)

    @api.depends("firstname", "othernames", "lastname", "lastname2")
    def _compute_name(self):
        """Write the 'name' according to splitted data."""
        for partner in self:
            partner.name = self._get_computed_name(
                partner.firstname, partner.othernames, partner.lastname, partner.lastname2)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
        domain = criteria_operator + [('identification_document', '=ilike', name + '%'), ('name', operator, name)]
        return self.search(domain + args, limit=limit).name_get()

    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))

        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(
                self._get_whitespace_cleaned_name(name),
                vals.get("is_company", self.default_get(["is_company"])["is_company"]),
            )
            for key, value in inverted.items():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                del vals["name"]
            if "default_name" in context:
                del context["default_name"]
            if "parent_id" in vals:
                vals["person_type"] = '2'
        return super(ResPartner, self.with_context(context)).create(vals)

    def copy(self, default=None):
        """Ensure partners are copied right.

        Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
        ignored in :meth:`~.create` because it also copies explicitly firstname
        and lastname fields.
        """
        return super(ResPartner, self.with_context(copy=True)).copy(default)

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(ResPartner, self).default_get(fields_list)

        inverted = self._get_inverse_name(self._get_whitespace_cleaned_name(result.get("name", "")),
                                          result.get("is_company", False),)

        for field in list(inverted.keys()):
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    @api.model
    def _names_order_default(self):
        return 'first_last'

    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        for record in self:
            parts = record._get_inverse_name(record.name, record.is_company)
            record.lastname = parts['lastname']
            record.lastname2 = parts['lastname2']
            record.firstname = parts['firstname']
            record.othernames = parts['othernames']

    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.
        You can override this method to read configuration from language,
        country, company or other"""
        return (self.env["ir.config_parameter"].sudo().get_param("partner_names_order", self._names_order_default()))

    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.

        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        for record in self:
            # Remove unneeded whitespace
            clean = record._get_whitespace_cleaned_name(record.name)
            record.name = clean
            record._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name, comma=False):
        """Remove redundant whitespace from :param:`name`.

        Removes leading, trailing and duplicated whitespace.
        """
        try:
            name = " ".join(name.split()) if name else name
        except UnicodeDecodeError:
            # with users coming from LDAP, name can be a str encoded as utf-8
            # this happens with ActiveDirectory for instance, and in that case
            # we get a UnicodeDecodeError during the automatic ASCII -> Unicode
            # conversion that Python does for us.
            # In that case we need to manually decode the string to get a
            # proper unicode string.
            name = " ".join(name.decode("utf-8").split()) if name else name

        if comma:
            name = name.replace(" ,", ",")
            name = name.replace(", ", ",")
        return name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.

        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.

        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes

        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        result = {
            'firstname': False,
            'othernames': False,
            'lastname': name or False,
            'lastname2': False,
        }
        if not is_company and name:
            order = self._get_names_order()
            # Remove redundant spaces
            name = self._get_whitespace_cleaned_name(
                name, comma=(order == "last_first_comma")
            )
            parts = name.split("," if order == "last_first_comma" else " ", 1)
            if len(parts) > 1:
                if order == "first_last":
                    parts = [" ".join(parts[1:]), parts[0]]
                else:
                    parts = [parts[0], " ".join(parts[1:])]
            else:
                while len(parts) < 2:
                    parts.append(False)
            result = {"lastname": parts[0], "firstname": parts[1]}
            parts = []
            # ___________________
            if order == 'last_first':
                if result['firstname']:
                    parts = result['firstname'].split(" ", 1)
                while len(parts) < 2:
                    parts.append(False)
                result['lastname2'] = parts[0]
                result['firstname'] = parts[1]
            else:
                if result['lastname']:
                    parts = result['lastname'].split(" ", 1)
                while len(parts) < 2:
                    parts.append(False)
                result['lastname'] = parts[0]
                result['lastname2'] = parts[1]
            # ___________________
            if order == 'first_last':
                if result['lastname2']:
                    parts = result['lastname2'].split(" ", 1)
                while len(parts) < 2:
                    result['othernames'] = False
                    return result
                result['othernames'] = result['lastname']
                result['lastname'] = parts[0]
                result['lastname2'] = parts[1]
            else:
                if result['firstname']:
                    parts = result['firstname'].split(" ", 1)
                while len(parts) < 2:
                    parts.append(False)
                result['firstname'] = parts[0]
                result['othernames'] = parts[1]
        return result

    # @api.constrains("firstname", "othernames", "lastname", "lastname2")
    # def _check_name(self):
    #     """Ensure at least one name is set."""
    #     for record in self:
    #         if all(
    #             (
    #                 record.type == "contact" or record.is_company,
    #                 not (record.firstname or record.lastname or 
    #                      record.othernames or record.lastname2),
    #             )
    #         ):
    #             raise exceptions.EmptyNamesError(record)

    @api.depends('identification_document')
    def _compute_same_identification_document_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            domain = [('identification_document', '=', partner.identification_document)]
            if partner_id:
                domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
            partner.same_identification_document_partner_id = bool(partner.identification_document) and not partner.parent_id and self.env['res.partner'].search(domain, limit=1)

    @api.constrains("identification_document")
    def _check_identification_document_unique(self):
        '''
        constrain temporal para cargue de datos
        mientras thomas define estructura fuerte en documento de indentificación
        '''
        for record in self:
            if record.parent_id or not record.identification_document:
                continue
            if record.same_identification_document_partner_id:
                raise ValidationError(
                    _("The Identification Document %s already exists in another partner.") % record.identification_document
                )

    @api.model
    def _install_partner_firstname(self):
        """Save names correctly in the database.

        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastname
        records = self.search([("firstname", "=", False), ("lastname", "=", False)])

        # Force calculations there
        records._inverse_name()
        _logger.info("%d partners updated installing module.", len(records))



    # Disabling SQL constraint givint a more explicit error using a Python
    # contstraint
    _sql_constraints = [("check_name", "CHECK( 1=1 )", "Contacts require a name.")]
