from abc import ABC, abstractmethod
from typing import Any, Generator


class BaseAnalyzer(ABC):
    def __init__(self, configs_file: str) -> None:
        self.configs = self.load_configs(configs_file)
        self.data_generator = self.load_data()

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
    def load_data(self) -> Generator:
        """Load data with self.configs or others

        Yields:
            Generator: Data with generator type, which can be generate/pop with get_current_data() method.
        """
        pass

    @abstractmethod
    def get_current_data(self) -> Any:
        """Yields batch of data by self.data_generator or others, which can be defined by configs.

        Returns:
            Any: Batch of data.
        """
        pass

    @abstractmethod
    def predict_step(self, data: Any) -> float:
        """Use model/algorithms/gpt/rulebase or anything to get a predict score.

        Args:
            data (Any): Data from the output of self.get_current_data().

        Returns:
            float: A predict score denote by
        """

        pass

    def forward(self):
        current_data = self.get_current_data()
        predict_results = self.predict_step(data=current_data)
        return predict_results
