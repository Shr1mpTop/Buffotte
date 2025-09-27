from setuptools import setup, find_packages

setup(
    name='buffotte',
    version='0.1.0',
    description='Buffotte market data crawler and forecast toolkit',
    packages=find_packages(),
    py_modules=['cli'],
    include_package_data=True,
    install_requires=[
        'requests', 'pymysql', 'pandas', 'scikit-learn', 'numpy', 'joblib', 'lightgbm', 'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'buffotte=cli:main'
        ]
    }
)
