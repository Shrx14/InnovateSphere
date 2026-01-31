def blend(conservative: float, optimistic: float) -> float:
    return 0.6 * max(conservative, 0) + 0.4 * max(optimistic, 0)
