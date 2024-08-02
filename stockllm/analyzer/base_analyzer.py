from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Tuple


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
        """Load data from local or internet by self.configs or others

        Yields:
            Generator: Data with generator type, which can be generate/pop with get_current_data() method.
        """
        pass

    @abstractmethod
    def get_current_data(self) -> Dict[str, Any]:
        """Yields batch of data by self.data_generator or others, which can be defined by configs.

        Returns:
            Dict[str, Any]: Batch of data and its ground truth.
                Ex.
                    {
                        "x": ["In celebration of Zoox’s 10th anniversary, NVIDIA founder, ...",
                              "Since 2014, Zoox has been on a mission to create fully autonomous, ..."],
                        "y": 937.6
                    }
                or
                    {
                        "x": [919.2, 905.9],
                        "y": 937.6
                    }
        """

        pass

    @abstractmethod
    def predict_step(self, data: Any) -> Tuple[float]:
        """Use model/algorithms/gpt/rulebase or anything to get a predict score.

        Args:
            data (Any): Data from the output of self.get_current_data().

        Returns:
            Tuple[float]: A score predicting whether a stock will rise or fall and its ground truth.
        """
        pass

    def __call__(self) -> float:
        current_data = self.get_current_data()
        predict_results = self.predict_step(data=current_data.get("x"))
        ground_truth = current_data.get("y")
        return predict_results, ground_truth
