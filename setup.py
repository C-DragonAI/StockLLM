from setuptools import setup, find_packages



description = """StockLLM leverages advanced Large Language Models (LLMs) to perform comprehensive stock market analysis and generate investment forecasting. By utilizing an innovative approach that integrates multiple indicators and applies ensemble learning techniques, StockLLM effectively predicts individual stock movements.

Users can easily forecast stock price trends by simply providing an API key, making sophisticated financial analysis accessible and user-friendly."""
setup(
    name='stockllm',
    version='0.0.1',
    packages=find_packages(),
    author=['Author 1', 'Author 2'], 
    author_email='TODO@email.com',
    description=description,
    url='https://github.com/C-DragonAI/StockLLM.git',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        'Programming Language :: Python :: 3.9',
    ],
    # TODO: Update the author and author_email fields with the correct information
    # TODO: Add any additional classifiers that are relevant to your project
    # TODO: Add any additional keywords that are relevant to your project
)