# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Module to repair mobile devices requiring mandatory IMEI numbers.

Adds IMEI fields in product category, product, and repair order models.
"""

from . import product_category
from . import product_template
from . import repair_order
