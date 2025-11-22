class UniverseManager:
    def __init__(self):
        # Common ETFs representing the indices and commodities
        self.etfs = [
            # 'SPY', 'IVV', 'VOO', # S&P 500 (US Market - Permission Denied)
            # 'QQQ', 'TQQQ', 'SQQQ', # Nasdaq 100 (US Market - Permission Denied)
            # 'GLD', 'IAU', 'SLV', # Gold/Silver (US Market - Permission Denied)
            # 'USO', 'UNG', # Oil/Gas (US Market - Permission Denied)
            # 'FXI', 'EWH', # China/HK related (US Market - Permission Denied)
            '2800', '02800', # HK Tracker Fund (HK Stock)
            '7200', '07200', # FL 2 HS 50 (HK Stock)
        ]
        
        # Major US stocks list removed as per user request. 
        # Agent is instructed to select from main index components in US and HK markets 
        # (represented here by ETFs and available HK stocks for now).
        
        self.major_hk_stocks = [
            '00700', '09988', '03690', '01299', '00941', '00005', '00388'
        ]
        
        self.universe = list(set(self.etfs + self.major_hk_stocks))

    def get_universe(self):
        """Returns the full list of tracked symbols."""
        return self.universe

    def get_random_sample(self, k=10):
        """Returns a random sample of symbols to analyze."""
        import random
        if len(self.universe) < k:
            return self.universe
        return random.sample(self.universe, k)

