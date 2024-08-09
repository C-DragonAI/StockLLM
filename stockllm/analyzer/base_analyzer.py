from abc import ABC, abstractmethod
from typing import Any


class BaseAnalyzer(ABC):
    """BaseAnalyzer is a unified analysis interface, which can be extended to analyze various aspects of stocks.

    Usage:
        analyzer = Analyzer(configs_file = "path/to/your/configs")
        prediction = analyzer.analysis()
    """

    def __init__(self, configs_file: str) -> None:
        self.configs = self.load_configs(configs_file)
        self.data = self.load_data()

    @abstractmethod
    def load_configs(self, configs_file: str) -> dict:
        """Create your configs file with any format, and implement this method to parse it.

        Args:
            configs_file (str): The path of configs file.

        Returns:
            dict: All configs or parameters for this analyzer.
        """
        pass

    @abstractmethod
    def load_data(self) -> Any:
        """Load data from local or internet by self.configs or others

        Returns:
            Any: Data during the past N days.
        """
        pass

    @abstractmethod
    def analysis(self) -> str:
        """Use model/algorithms/gpt/rulebase or anything to get a prediction by self.data.

        Returns:
            str: Summary of its aspect analysis and the prediction of the next day.
        """
        pass
