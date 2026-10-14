"""
Mock LLM thông minh - trả lời đa dạng theo ngữ cảnh hội thoại.
"""
import random
from .base import LLMClient


class MockLLM(LLMClient):
    
    TOPIC_RESPONSES = {
        "buồn": [
            "Mình hiểu em đang buồn. Điều đó hoàn toàn bình thường thôi. Em có muốn kể thêm cho mình nghe không? Mình đang lắng nghe đây. 😊",
            "Buồn là cảm xúc tự nhiên, em không cần phải giấu đâu. Mình ở đây với em. Em thử hít thở sâu 3 lần xem sao — hít vào chậm, thở ra chậm nhé.",
            "Nghe em kể, mình thấy em đang chịu đựng nhiều. Cảm ơn em đã tin tưởng chia sẻ. Em thử đánh giá cảm xúc hôm nay theo 5 mức xem sao — từ 1 rất buồn đến 5 rất vui.",
        ],
        "căng_thẳng": [
            "Căng thẳng trước áp lực là bình thường thôi. Mình thử cùng nhau thở 4-7-8 nha: hít vào 4 giây, giữ hơi 7 giây, thở ra chậm 8 giây. Làm 3 lần sẽ thấy dịu hơn. Em thử xem?",
            "Mình hiểu áp lực làm em căng thẳng. Em thử chia nhỏ công việc ra xem sao — làm từng bước một, không cần hoàn hảo ngay. Em đang lo lắng về điều gì nhất?",
            "Căng thẳng quá thì mình nghỉ ngơi một chút cũng được. Em thử đứng dậy vươn vai, uống nước, hoặc nghe một bài hát em thích. Sau đó mình quay lại nói chuyện tiếp nhé.",
        ],
        "giận_dữ": [
            "Mình hiểu em đang giận. Cảm xúc đó hoàn toàn hợp lý. Em thử hít thở sâu vài lần, hoặc đi bộ một vòng cho nhẹ lòng. Khi bình tĩnh hơn, mình cùng nghĩ cách giải quyết nhé?",
            "Giận dữ là tín hiệu rằng có điều gì đó không ổn. Em có muốn kể rõ hơn cho mình nghe không? Đôi khi viết ra giấy sẽ giúp em thấy nhẹ hơn.",
        ],
        "cô_đơn": [
            "Cảm thấy cô đơn là trải nghiệm khó khăn. Nhưng em biết không, nhiều người cũng cảm thấy vậy. Em có ai em tin tưởng để nói chuyện không? Cô Dung, bố mẹ, hay một người bạn?",
            "Mình hiểu cảm giác cô đơn. Đôi khi mình chỉ cần ai đó lắng nghe thôi. Mình đang lắng nghe em đây. Em có muốn kể thêm không?",
        ],
        "bắt_nạt": [
            "Bị bắt nạt KHÔNG phải lỗi của em. Em không đáng bị đối xử như vậy. Em có dám nói với cô Dung hoặc bố mẹ không? Nếu không biết nói sao, mình cùng nghĩ cách nha.",
            "Mình rất lo khi nghe em kể. Đây là điều nghiêm trọng. Em hãy nói ngay với người lớn em tin — cô giáo, bố mẹ, hoặc gọi 111. Em không cần chịu đựng một mình.",
        ],
        "gia_đình": [
            "Gia đình là nơi quan trọng nhất, nhưng cũng có lúc phức tạp. Em có muốn kể thêm không? Mình đang lắng nghe đây.",
            "Nếu ở nhà em thấy không an toàn, hãy nói ngay với cô Dung hoặc gọi 111. Em không cần phải chịu đựng một mình.",
        ],
        "học_tập": [
            "Điểm số không nói lên tất cả. Quan trọng là em hiểu bài và cố gắng. Em thử xem lại cách học — có cần đổi phương pháp không?",
            "Nếu em thấy học quá áp lực, hãy nghỉ ngơi một chút. Đi bộ, nghe nhạc, hoặc nói chuyện với ai đó. Sau đó quay lại học với tâm trạng nhẹ nhàng hơn.",
        ],
        "mặc_định": [
            "Mình hiểu rồi. Em kể thêm cho mình nghe đi, mình đang lắng nghe đây. 😊",
            "Cảm ơn em đã chia sẻ. Em có muốn thử đánh giá cảm xúc hôm nay theo 5 mức không? Từ 1 rất buồn đến 5 rất vui.",
            "Mình ở đây với em. Em thử ghi lại theo mô hình ABC xem: A - việc xảy ra, B - cách em nghĩ, C - cảm xúc của em.",
            "Em ơi, cảm xúc của em là hợp lý. Mình không phán xét gì đâu. Em cứ thoải mái chia sẻ nhé.",
        ],
    }
    
    TOPIC_KEYWORDS = {
        "buồn": ["buồn", "khóc", "chán", "thất vọng", "không vui", "cô giáo mắng"],
        "căng_thẳng": ["căng thẳng", "stress", "áp lực", "lo lắng", "sắp thi", "thi cử"],
        "giận_dữ": ["giận", "tức", "bực bội", "khó chịu"],
        "cô_đơn": ["cô đơn", "một mình", "không ai", "lẻ loi"],
        "bắt_nạt": ["bắt nạt", "đe dọa", "làm hại", "xúc phạm"],
        "gia_đình": ["bố mẹ", "cha mẹ", "gia đình", "anh chị em"],
        "học_tập": ["học", "bài tập", "thi", "điểm số", "cô giáo", "thầy giáo"],
    }
    
    def _classify_topic(self, text: str) -> str:
        text_lower = text.lower()
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        return "mặc_định"
    
    def _get_response(self, topic: str) -> str:
        responses = self.TOPIC_RESPONSES.get(topic, self.TOPIC_RESPONSES["mặc_định"])
        return random.choice(responses)
    
    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        last_msg = messages[-1]["content"] if messages else ""
        text = last_msg.lower()
        
        # Crisis detection
        if any(kw in text for kw in ["muốn chết", "tự tử", "chết đi", "không muốn sống"]):
            return "Em ơi, mình rất lo cho em lúc này. Hãy gọi ngay Tổng đài 111 - miễn phí, 24/7. Hoặc tìm cô Dung hay người lớn mà em tin nhất. Mình vẫn ở đây với em."
        
        # Jailbreak protection
        if any(kw in text for kw in ["bỏ vai trò", "giả sử bạn là", "ignore previous"]):
            return "Mình không thể thay đổi vai trò. Mình là Người bạn nhỏ AI - người bạn đồng hành của em. Em có muốn kể chuyện gì không? "
        
        # Classify and respond
        topic = self._classify_topic(text)
        return self._get_response(topic)
