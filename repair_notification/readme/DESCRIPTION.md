This module extends the standard Repair application to improve customer communication during the repair process.

It adds new configuration options in the Repair application settings allowing users to:

- Enable or disable automatic email notifications when a repair starts

- Enable or disable automatic email notifications when a repair ends

- Select a specific email template for each notification type (start and end)

When enabled, an email is automatically sent to the customer:

- When the repair order moves to the in progress state

- When the repair order is completed

To avoid duplicate notifications, the module ensures that the “repair start” email is sent only once per repair order.
If a repair is started, then cancelled, and later restarted, the customer will not receive the start notification again.
