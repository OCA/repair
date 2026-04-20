**BUSINESS NEED:**

This module addresses the need for businesses to use a dedicated email address for repair-order-related communications. This ensures that customer replies are directed to the appropriate mailbox, improving response times and customer satisfaction.

**RATIONALE**

While Odoo Mail Templates provide "From" and "Reply-To" fields, they are often insufficient for this requirement due to Odoo's core threading architecture:

* **Catchall Override:** When an email is sent from a document inheriting `mail.thread` (like `repair.order`), Odoo's notification logic automatically overrides the `Reply-To` header to the system's catchall address. This is designed to force conversations into the Odoo chatter.
* **Inconsistent Headers:** Relying solely on templates can lead to "From" and "Reply-To" headers being out of sync.
* **Manual Mail Support:** By overriding the logic at the model level, the custom email is used consistently even when a user sends a manual message without selecting a specific template.

**USEFUL INFORMATION:**

- Works well in multi-company setups where each company may have its own repair email address.
