/* Original demonstration code: no benchmark labels or known-defect claims. */
int clamp_index(int value, int count) {
    if (value < 0) return 0;
    if (value >= count) return count - 1;
    return value;
}

int sum_values(const int *values, int count) {
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += values[i];
    }
    return total;
}

int entry(void) {
    int values[3] = {1, 2, 3};
    return sum_values(values, 3);
}
