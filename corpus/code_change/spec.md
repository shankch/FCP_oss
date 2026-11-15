# Change request C-STUDENT-1: student pricing at Fernwood Outfitters

`checkout.py` holds the checkout function of our online store, and `test_checkout.py` its tests. Change the function as follows, and update the tests:

    def checkout(subtotal: int, coupon: int, member: bool, student: bool = False) -> tuple[int, int]:

1. Students get 15% off. This adds to the other discounts, and the total discount is still never more than 30%.
2. Free shipping now starts at $75 instead of $50.
3. Nothing may change for customers who are not students.
4. Keep everything else as it is.

Example: a student with a $100.00 cart, no coupon and no membership gets `(8500, 0)`.
