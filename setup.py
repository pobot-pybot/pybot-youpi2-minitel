from setuptools import setup, find_packages

setup(
    name='pybot-youpi2-minitel',
    setup_requires=['setuptools_scm'],
    use_scm_version={
        'write_to': 'src/pybot/youpi2nitel/__version__.py'
    },
    namespace_packages=['pybot'],
    packages=find_packages("src"),
    package_dir={'': 'src'},
    url='',
    license='',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    install_requires=['pybot-core', 'pybot-dspin', 'pybot-youpi2'],
    download_url='https://github.com/Pobot/PyBot',
    description='Library for Youpi arm controlled by STMicro L6470 (aka dSPIN)',
    entry_points={
        'console_scripts': [
            'youpi2-minitel = pybot.youpi2nitel.toplevel:main'
        ]
    }
)