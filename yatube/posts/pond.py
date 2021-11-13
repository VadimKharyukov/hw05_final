def effective_quick_sorts(array):
    def quick_sorts(left, right):
        if left >= right:
            return array
        start = left
        for element in range(left, right):
            if array[right] > array[element]:
                array[start], array[element] = array[element], array[start]
                start += 1
        array[start], array[right] = array[right], array[start]

        quick_sorts(left, start - 1)
        quick_sorts(start + 1, right)

    quick_sorts(0, len(array) - 1)
    return array


if __name__ == "__main__":
    print(
        *(login for _, _, login in effective_quick_sorts(
            [(lambda *args: (-int(args[1]), int(args[2]), args[0]))(
                *input().split()) for _ in range(int(input()))],
        )),
        sep="\n")
