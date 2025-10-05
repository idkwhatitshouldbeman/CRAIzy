class CardTracker:
    def __init__(self, deck):
        self.deck = deck
        self.hand = deck[:4].copy()  # Current 4 cards
        self.next_index = 4  # Cycle from deck[4:]

    def card_played(self, slot):
        if slot is None:
            return None
        played = self.hand[slot]
        self.hand[slot] = self.deck[self.next_index % len(self.deck)]
        self.next_index += 1
        return played  # Logging only
