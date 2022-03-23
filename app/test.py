class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
        a, b, c = [], "", ""
        b += str(l1.val)
        c += str(l2.val)
        while l1.next:
            b += str(l1.next.val)
            l1 = l1.next
        while l2.next:
            c += str(l2.next.val)
            l2 = l2.next
        b = reversed(b)
        c = reversed(c)
        a = str(b) + str(c)
        return a


if __name__ == '__main__':
    a = ListNode(2)
    a.next = ListNode(4)
    a.next.next = ListNode(3)
    b = ListNode(5)
    b.next = ListNode(6)
    b.next.next = ListNode(4)
    print(Solution.addTwoNumbers(Solution, a, b))
