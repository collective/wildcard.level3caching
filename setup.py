from setuptools import setup, find_packages
import os

version = '1.1a3'

setup(name='wildcard.level3caching',
      version=version,
      description="provide integration for invalidations with level3",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone level3 caching cdn',
      author='Nathan Van Gheem',
      author_email='nathan.vangheem@wildcardcorp.com',
      url='http://svn.plone.org/svn/collective/wildcard.level3caching',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['wildcard'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
