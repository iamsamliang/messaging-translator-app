function binarySearch(arr: number[], target: number): number {
    let low = 0;
    let high = arr.length - 1;

    while (low <= high) {
        const mid = Math.floor(low + (high - low) / 2);
        const guess = arr[mid];

        if (guess === target) {
            return mid;
        } else if (guess > target) {
            high = mid - 1;
        } else {
            low = mid + 1;
        }
    }

    return -1; // Item not found
}

export function deleteFromSortedArray(arr: number[], item: number): void {
    const index = binarySearch(arr, item);
    if (index !== -1) arr.splice(index, 1);
}