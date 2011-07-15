#!/usr/bin/python
#	vim:fileencoding=utf-8
# (c) 2011 Michał Górny <mgorny@gentoo.org>
# Released under the terms of the 2-clause BSD license.

from portage.versions import cpv_getkey, cpv_getversion, vercmp, \
		catsplit

from gentoopm.basepm.metadata import PMPackageMetadata
from gentoopm.basepm.pkg import PMPackage
from gentoopm.basepm.pkgset import PMPackageSet, PMFilteredPackageSet
from gentoopm.portagepm.atom import PortageAtom

class PortagePackageSet(PMPackageSet):
	def filter(self, *args, **kwargs):
		newargs = [(a if not isinstance(a, str)
			else PortageAtom(a)) for a in args]

		return PortageFilteredPackageSet(self, newargs, kwargs)

class PortageFilteredPackageSet(PortagePackageSet, PMFilteredPackageSet):
	pass

class PortageDBCPV(PMPackage):
	def __init__(self, cpv, dbapi):
		self._cpv = cpv
		self._dbapi = dbapi

	@property
	def metadata(self):
		return PortageDBMetadata(self._cpv, self._dbapi)

	@property
	def path(self):
		# .findname() gives .ebuild path
		return self._dbapi.getpath(self._cpv)

	@property
	def atom(self):
		return PortageAtom('=%s' % self._cpv, self)

	def __lt__(self, other):
		if not isinstance(other, PortageDBCPV):
			raise TypeError('Unable to compare %s against %s' % \
					(self, other))
		return cpv_getkey(self._cpv) < cpv_getkey(other._cpv) \
				or vercmp(cpv_getversion(self._cpv), cpv_getversion(other._cpv)) < 0

class PortageCPV(PortageDBCPV):
	def __init__(self, cpv, dbapi, tree, repo_prio):
		PortageDBCPV.__init__(self, cpv, dbapi)
		self._tree = tree
		self._repo_prio = repo_prio

	@property
	def metadata(self):
		return PortageMetadata(self._cpv, self._dbapi, self._tree)

	@property
	def path(self):
		return self._dbapi.findname(self._cpv, self._tree)

	@property
	def atom(self):
		return PortageAtom('=%s::%s' % (self._cpv,
			self._dbapi.getRepositoryName(self._tree)), self)

	def __lt__(self, other):
		if not isinstance(other, PortageCPV):
			raise TypeError('Unable to compare %s against %s' % \
					(self, other))
		return cpv_getkey(self._cpv) < cpv_getkey(other._cpv) \
				or vercmp(cpv_getversion(self._cpv), cpv_getversion(other._cpv)) < 0 \
				or self._repo_prio < other._repo_prio

class PortageDBMetadata(PMPackageMetadata):
	def __init__(self, cpv, dbapi):
		self._cpv = cpv
		self._dbapi = dbapi

	def __getattr__(self, key):
		if key not in self:
			raise AttributeError('Unsupported metadata key: %s' % key)
		return self._dbapi.aux_get(self._cpv, [key])[0]

	@property
	def CATEGORY(self):
		return catsplit(self._cpv)[0]

class PortageMetadata(PortageDBMetadata):
	def __init__(self, cpv, dbapi, tree):
		PortageDBMetadata.__init__(self, cpv, dbapi)
		self._tree = tree

	def __getattr__(self, key):
		if key not in self:
			raise AttributeError('Unsupported metadata key: %s' % key)
		return self._dbapi.aux_get(self._cpv, [key],
				mytree = self._tree)[0]
