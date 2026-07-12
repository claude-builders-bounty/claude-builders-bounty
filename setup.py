from setuptools import setup, find_packages

setup(
    name='claude-review',
    version='0.1.0',
    description='AI-powered PR review tool',
    author='Claude Builders',
    author_email='claude.builders@example.com',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'PyGithub>=1.55'
    ],
    entry_points={
        'console_scripts': [
            'claude-review = claude_review.cli:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    python_requires='>=3.7'
)