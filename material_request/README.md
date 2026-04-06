# Material Request

This module handles the flow for site engineers to request materials for their projects. It's designed to keep things straightforward: engineers request items, and project managers approve them to generate RFQs.

## Workflow

1.  **Create Request**: A user usually a site engineer creates a new request and picks the project.
2.  **Add Lines**: They list out the products and quantities needed. I added some basic checks here so you can't submit without lines or with zero quantity.
3.  **Submit**: Clicking 'Submit' moves it to the submitted state and pings the project manager.
4.  **Approve**: The Project Manager reviews it. So they click 'Approve'.
    *   *Note*: This action automatically creates a Purchase Order (RFQ).
    *   Only users with the "Project Manager" group can do this.
5.  **RFQs**: You can see the created RFQs via the smart button at the top.



## Restrictions

*   You can't delete a request once it's approved (for audit purposes).
*   You can't approve the same request twice (it checks if an RFQ is already linked).



## Project Integration

I have also updated the Project form so you can see everything in one place:

*   **Material Requests Tab**: There's a new tab on the project called "Material Requests". It lists every request linked to that project.
*   **Material Cost**: You'll see a computed field showing the total cost. It basically sums up all the RFQs from those requests (ignoring the cancelled ones).


