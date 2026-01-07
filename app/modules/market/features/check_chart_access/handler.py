class CheckChartAccessHandler:
    def handle(self, user_tier: str):
        # Logic đơn giản: ai login cũng được xem, nhưng trả về info khác nhau
        return {
            "allow_chart": True,
            "user_tier": user_tier,
            "message": "Bạn được phép truy cập thị trường."
        }