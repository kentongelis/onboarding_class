# A customer wants to pay for a purchase using exactly two gift cards. 
# Given a list of gift card balances and the purchase total, return the positions of the two cards 
# whose balances add up to exactly the total. Assume there is exactly one answer, and a card can't be 
# used twice.

# balances = [25, 10, 40, 12, 30], total = 55   →   [0, 4]   (25 + 30)

def balances(balances, target):
    seen = {}
    for i in range(len(balances)):
        need = target - balances[i]
        if need in seen:
            return [i, seen[need]]
        seen[balances[i]] = i

print(balances([25, 10, 40, 12, 30], 55))

# Time Complexity: 0(n) one pass through, O(1) lookups through the dictionary
# Space Complexity: O(n) because dictionary was created 