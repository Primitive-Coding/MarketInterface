from transformers import BertModel, BertTokenizer


class SentimentAnalysis:
    def __init__(
        self, model_name: str = "bert-base-uncased", model_path: str = "M:\\Models\\"
    ) -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def set_model(self):
        self.model, self.tokenizer = self.load_model()

    def load_model(self):
        model = BertModel.from_pretrained(self.model_path)
        tokenizer = BertTokenizer.from_pretrained(self.model_path)
        return model, tokenizer

    def save_model(self):
        self.model.save_pretrained(self.model_path)
        self.tokenizer.save_pretrained(self.model_path)
