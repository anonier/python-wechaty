class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        a, b = [], []
        for i, j in enumerate(s):
            if len(b) <= 0:
                b.append(j)
            else:
                try:
                    b.index(j)
                    for y in range(len(b)):
                        try:
                            b[y:].index(j)
                            if y == len(b) - 1:
                                a = b
                                b = [j]
                            continue
                        except:
                            if len(b) > len(a):
                                a = b
                            b = b[y:]
                            break

                except:
                    b.append(j)

        return len(b) if len(b) > len(a) else len(a)


if __name__ == '__main__':
    print(Solution.lengthOfLongestSubstring(Solution, "abcabcbb"))
