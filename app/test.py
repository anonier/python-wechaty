class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
        b = l1.val
        c = l2.val
        l = 10
        while l1.next:
            if l1.next is None:
                b += l1.next.val * l
                l1 = l1.next
            if l2.next is None:
                c += l2.next.val * l
                l2 = l2.next
            l *= l
        a = b + c
        root = ListNode(a % 10)
        a = int(a / 10)
        top = root
        while a >= 1:
            d = ListNode(a % 10)
            a = int(a / 10)
            top.next = d
            top = top.next
        return root


if __name__ == '__main__':
    a = ListNode(2)
    a.next = ListNode(4)
    a.next.next = ListNode(3)
    b = ListNode(5)
    b.next = ListNode(6)
    b.next.next = ListNode(4)
    print(Solution.addTwoNumbers(Solution, a, b))
