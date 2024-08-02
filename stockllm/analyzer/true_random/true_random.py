from typing import Any, Dict, Tuple
from stockllm.analyzer.base_analyzer import BaseAnalyzer
import requests


class TrueRandomAnalyzer(BaseAnalyzer):
    
    def __init__(self) -> None:
        super().__init__(None)

    def predict_step(self, data: Any) -> Tuple[float]:
        # generates a random number R either 1,2,3
        # when R == 1 it's a TIE
        # when R == 2 it's a RISE
        # when R == 3 it's a FALL
        url = """https://www.random.org/integers/?num=1&min=1&max=3&col=5&base=10&format=plain&rnd=new"""
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to get random number from random.org")
        return int(response.text)
    
    def load_configs(self, configs_file: str) -> dict:
        pass
    
    def load_data(self):
        pass
    
    def get_current_data(self) -> Dict[str, Any]:
        pass



if __name__ == "__main__":
    analyzer = TrueRandomAnalyzer()
    print(analyzer.predict_step(None))
