

def analyze_text_with_perplexity(text: str) -> dict:
    """
    Sentiment analysis using only TextBlob (AI/Perplexity API removed).
    Returns: {
        'sentiment_label': str,  # Positive, Negative, Neutral
        'sentiment_score': float,  # 0-1
        'emotion_label': str,     # (empty)
        'aspect_scores': dict     # clarity, interaction, punctuality, fairness
    }
    """
    return textblob_sentiment(text)


def textblob_sentiment(text: str) -> dict:
    try:
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        # Map polarity to label and score
        if polarity > 0.3:
            label = "Positive"
        elif polarity < -0.3:
            label = "Negative"
        else:
            label = "Neutral"
        score = abs(polarity)
        return {
            "sentiment_label": label,
            "sentiment_score": score,
            "emotion_label": "",
            "aspect_scores": aspect_sentiment_stub(text)
        }
    except Exception as e:
        print(f"[Analyzer] TextBlob fallback failed: {e}")
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.0,
            "emotion_label": "",
            "aspect_scores": aspect_sentiment_stub(text)
        }


def aspect_sentiment_stub(text: str) -> dict:
    """
    Simple keyword-based aspect sentiment stub for clarity, interaction, punctuality, fairness.
    Returns a dict of aspect: score (0-1)
    """
    aspects = {
        'clarity': ["clear", "confusing", "understand", "explain"],
        'interaction': ["interactive", "questions", "discussion", "engage"],
        'punctuality': ["late", "on time", "punctual", "delay"],
        'fairness': ["fair", "biased", "partial", "unfair"]
    }
    text_lower = text.lower()
    aspect_scores = {}
    for aspect, keywords in aspects.items():
        score = 0.0
        for kw in keywords:
            if kw in text_lower:
                score += 0.25
        aspect_scores[aspect] = min(score, 1.0)
    return aspect_scores
