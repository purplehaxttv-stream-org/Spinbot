"""Legacy CLI raffle with weighted random selection."""
import random


class Raffle:
    """Weighted raffle that picks a winner from (name, weight) entries."""
    def __init__(self, entries):
        """entries: list of (display_name, weight) tuples"""
        self.entries = [(name, weight) for name, weight in entries if weight > 0]
        self.total = sum(w for _, w in self.entries)

    @property
    def entrant_count(self):
        """Return the number of valid entrants."""
        return len(self.entries)

    def pick_winner(self):
        """Return a randomly selected winner, weighted by entry count."""
        if not self.entries:
            return None
        names, weights = zip(*self.entries)
        return random.choices(names, weights=weights, k=1)[0]

    def get_chance(self, name):
        """Return the win probability for a given entrant as a percentage."""
        for n, w in self.entries:
            if n == name:
                return w / self.total * 100
        return 0.0

    def display(self):
        """Return a formatted string showing all entrants and their odds."""
        lines = []
        lines.append(f"Giveaway - {self.entrant_count} entrants, {self.total} total entries\n")
        for name, count in self.entries:
            pct = count / self.total * 100
            bar = "#" * int(pct)
            lines.append(f"  {name:<20} {count:>3} entries ({pct:5.1f}%) {bar}")
        return "\n".join(lines)
