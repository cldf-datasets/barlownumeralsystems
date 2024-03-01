from setuptools import setup


setup(
    name='cldfbench_barlownumeralsystems',
    py_modules=['cldfbench_barlownumeralsystems'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'barlownumeralsystems=cldfbench_barlownumeralsystems:Dataset',
        ]
    },
    install_requires=[
        'cldfbench[glottolog]',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
