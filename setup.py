from setuptools import setup, find_packages

setup(
    name='pybot-youpi2-minitel',
    setup_requires=['setuptools_scm'],
    use_scm_version={
        'write_to': 'src/pybot/youpi2/minitel/__version__.py'
    },
    namespace_packages=['pybot'],
    packages=find_packages("src"),
    package_dir={'': 'src'},
    url='',
    license='',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    install_requires=['pybot-core', 'pybot-dspin', 'pybot-youpi2', 'pybot-minitel'],
    download_url='https://github.com/Pobot/PyBot',
    description='Youpi2 Minitel control UI',
    entry_points={
        'console_scripts': [
            'youpi2-minitel = pybot.youpi2.minitel.toplevel:main'
        ]
    }
)
