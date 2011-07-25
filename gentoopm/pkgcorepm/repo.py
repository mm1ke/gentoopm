#!/usr/bin/python
#	vim:fileencoding=utf-8
# (c) 2011 Michał Górny <mgorny@gentoo.org>
# Released under the terms of the 2-clause BSD license.

from abc import abstractproperty

import pkgcore.restrictions.boolean as br

from gentoopm.basepm.repo import PMRepository, PMRepositoryDict, \
		PMEbuildRepository
from gentoopm.pkgcorepm.pkg import PkgCorePackageSet, PkgCoreFilteredPackageSet, \
		PkgCoreInstallablePackage, PkgCoreInstalledPackage
from gentoopm.pkgcorepm.filter import transform_filters
from gentoopm.util import FillMissingComparisons

class PkgCoreRepoDict(PMRepositoryDict):
	def __iter__(self):
		for i, r in enumerate(self._stack.trees):
			yield PkgCoreEbuildRepo(r, self._domain, i)

	def __init__(self, stack, domain):
		self._stack = stack
		self._domain = domain

class PkgCoreRepository(PkgCorePackageSet, PMRepository):
	_index = 0
	def __init__(self, repo_obj, domain):
		self._repo = repo_obj.configure(repo_obj, domain,
				domain.settings)

	@abstractproperty
	def _pkg_class(self):
		pass

	def __iter__(self):
		index = self._index
		for pkg in self._repo:
			yield self._pkg_class(pkg, index)

	def filter(self, *args, **kwargs):
		r = self
		filt, newargs, newkwargs = transform_filters(args, kwargs)

		if filt:
			r = PkgCoreFilteredRepo(self, filt)
		if newargs or newkwargs:
			r = PkgCoreFilteredPackageSet(r, args, kwargs)

		return r

class PkgCoreFilteredRepo(PkgCoreRepository):
	def __init__(self, repo, filt):
		self._repo = repo
		self._filt = filt
		self._index = repo._index

	@property
	def _pkg_class(self):
		return self._repo._pkg_class

	def __iter__(self):
		index = self._index
		for pkg in self._repo._repo.match(self._filt):
			yield self._pkg_class(pkg, index)

	def filter(self, *args, **kwargs):
		r = self
		filt, newargs, newkwargs = transform_filters(args, kwargs)

		if filt:
			r = PkgCoreFilteredRepo(self._repo,
					br.AndRestriction(self._filt, filt))
		if newargs or newkwargs:
			r = PkgCoreFilteredPackageSet(r, args, kwargs)

		return r

class PkgCoreEbuildRepo(PkgCoreRepository, PMEbuildRepository,
		FillMissingComparisons):

	_pkg_class = PkgCoreInstallablePackage

	def __init__(self, repo_obj, domain, index):
		PkgCoreRepository.__init__(self, repo_obj, domain)
		self._index = index

	@property
	def name(self):
		return self._repo.repo_id

	@property
	def path(self):
		return self._repo.location

	def __lt__(self, other):
		return other._index < self._index

class PkgCoreInstalledRepo(PkgCoreRepository):
	_pkg_class = PkgCoreInstalledPackage
