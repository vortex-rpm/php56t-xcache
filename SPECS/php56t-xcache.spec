# Vortex RPM spec file forked from:
#
# IUS spec file for php56u-xcache, forked from:
#
# Fedora spec file for php-xcache
#
# Copyright (c) 2012-2014 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Please, preserve the changelog entries
#
%{!?php_inidir:  %global php_inidir       %{_sysconfdir}/php.d}
%global ext_name     xcache
%global with_zts     0%{?__ztsphp:1}

%global ini_name  40-%{ext_name}.ini

%global php php56t

Summary:       Fast, stable PHP opcode cacher
Name:          %{php}-%{ext_name}
Epoch:         1
Version:       3.2.0
Release:       1.vortex%{?dist}
License:       BSD
Vendor:        Vortex RPM
Group:         Development/Languages
URL:           http://xcache.lighttpd.net/
Source0:       http://xcache.lighttpd.net/pub/Releases/%{version}/%{ext_name}-%{version}.tar.gz
Source1:       xcache-httpd.conf

# Relocation of configuration files to /etc/xcache
Patch0:        xcache-config.patch
# Disable cache to allow work with php-opcache
Patch1:        xcache-cacher.patch

BuildRequires: %{php}-devel

Requires:      %{php}(zend-abi) = %{php_zend_api}
Requires:      %{php}(api) = %{php_core_api}

Provides:      php-%{ext_name} = %{epoch}:%{version}-%{release}
Provides:      php-%{ext_name}%{?_isa} = %{epoch}:%{version}-%{release}

Conflicts:     php-%{ext_name} < %{epoch}:%{version}

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter private shared object
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
XCache is a fast, stable  PHP opcode and data cacher that has been tested
and is now running on production servers under high load.

It is tested (on linux) and supported on all of the latest PHP release.
ThreadSafe is also perfectly supported.

NOTICE: opcode cacher is disable to allow use with php-opcache only for user
data cache. You need to edit configuration file (xcache.ini) to enable it.


%package admin
Summary:       XCache Administration
Group:         Development/Languages
Requires:      %{name} = %{epoch}:%{version}-%{release}
BuildArch:     noarch

Provides:      xcache-admin = %{epoch}:%{version}-%{release}
Conflicts:     xcache-admin < %{epoch}:%{version}

%description admin
This package provides the XCache Administration web application.

This requires to configure, in XCache configuration file (xcache.ini):
- xcache.admin.user
- xcache.admin.pass
- xcache.coveragedump_directory


%prep
%setup -q -c

# rename source folder
mv xcache-%{version} nts

cp %{SOURCE1} xcache-httpd.conf
cd nts
%patch0 -p1
%patch1 -p1

# Sanity check, really often broken
extver=$(sed -n '/define XCACHE_VERSION/{s/.* "//;s/".*$//;p}' xcache.h)
if test "x${extver}" != "x%{version}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}.
   exit 1
fi
cd ..

%if %{with_zts}
# duplicate for ZTS build
cp -pr nts zts
%endif


%build
# Without --enable-xcache-assembler, --enable-xcache-encoder, --enable-xcache-decoder
# This seems not yet implemented

cd nts
%{_bindir}/phpize
%configure \
    --enable-xcache \
    --enable-xcache-constant \
    --enable-xcache-optimizer \
    --enable-xcache-coverager \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../zts
%{_bindir}/zts-phpize
%configure \
    --enable-xcache \
    --enable-xcache-constant \
    --enable-xcache-optimizer \
    --enable-xcache-coverager \
    --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
# Install the NTS stuff
make -C nts install INSTALL_ROOT=%{buildroot}
install -D -m 644 nts/%{ext_name}.ini %{buildroot}%{php_inidir}/%{ini_name}

%if %{with_zts}
# Install the ZTS stuff
make -C zts install INSTALL_ROOT=%{buildroot}
install -D -m 644 zts/%{ext_name}.ini %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Install the admin stuff
install -d -m 755 %{buildroot}%{_datadir}
cp -pr nts/htdocs %{buildroot}%{_datadir}/xcache
install -d -m 755 %{buildroot}%{_sysconfdir}/xcache/cacher
install -d -m 755 %{buildroot}%{_sysconfdir}/xcache/coverager
mv %{buildroot}%{_datadir}/xcache/config.example.php \
   %{buildroot}%{_sysconfdir}/xcache
mv %{buildroot}%{_datadir}/xcache/cacher/config.example.php \
   %{buildroot}%{_sysconfdir}/xcache/cacher
mv %{buildroot}%{_datadir}/xcache/coverager/config.example.php \
   %{buildroot}%{_sysconfdir}/xcache/coverager


%check
cd nts

# simple module load test
%{__php} --no-php-ini \
    --define extension_dir=%{buildroot}%{php_extdir}/\
    --define extension=%{ext_name}.so \
    --modules | grep XCache

# upstream unit tests
TEST_PHP_EXECUTABLE=%{__php} \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php -n -c xcache-test.ini tests

%if %{with_zts}
cd ../zts
%{__ztsphp} --no-php-ini \
    --define extension_dir=%{buildroot}%{php_ztsextdir}/\
    --define extension=%{ext_name}.so \
    --modules | grep XCache

TEST_PHP_EXECUTABLE=%{__ztsphp} \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php -n -c xcache-test.ini tests
%endif


%files
%doc nts/{AUTHORS,ChangeLog,COPYING,README,THANKS}
%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{ext_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{ext_name}.so
%endif

%files admin
%doc xcache-httpd.conf
%{_datadir}/xcache
# No real configuration files, only sample files
%{_sysconfdir}/xcache


%changelog
* Fri Jul 24 2015 Ilya Otyutskiy <ilya.otyutskiy@icloud.com> - 1:3.2.0-1.vortex
- Rebuilt with php56t.

* Wed Jul 08 2015 Carl George <carl.george@rackspace.com> 1:3.2.0-1.ius
- Port from Fedora to IUS

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:3.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu Sep 18 2014 Remi Collet <remi@fedoraproject.org> - 1:3.2.0-1
- Update to 3.2.0

* Tue Sep  9 2014 Remi Collet <remi@fedoraproject.org> - 1:3.2.0-0.1.rc1
- Update to 3.2.0-rc1
- bump epoch to 1

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0.0-0.2.svn1496
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun  7 2014 Remi Collet <remi@fedoraproject.org> - 4.0.0-0.1.svn1496
- Update to 4.0.0-dev for PHP 5.6
- add numerical prefix to configuration file

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Jan  9 2014 Remi Collet <remi@fedoraproject.org> - 3.1.0-2
- drop conflicts with other opcode cache
- disable opcode cache in provided configuration

* Sat Oct 12 2013 Remi Collet <remi@fedoraproject.org> - 3.1.0-1
- version 3.1.0

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-0.3.svn1264
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jun 14 2013 Remi Collet <remi@fedoraproject.org> - 3.1.0-0.2.svn1268
- latest changes from upstream

* Tue Apr 16 2013 Remi Collet <remi@fedoraproject.org> - 3.1.0-0.1.svn1234
- update to SVN snapshot for php 5.5 compatibility

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Jan 17 2013 Remi Collet <remi@fedoraproject.org> - 3.0.1-1
- bugfixes version

* Thu Nov 22 2012 Remi Collet <remi@fedoraproject.org> - 3.0.0-1.1
- upstream have fixed the sources (review #859504)

* Wed Oct 31 2012 Remi Collet <remi@fedoraproject.org> - 3.0.0-1
- new major version
- drop xcache-coverager subpackage
- xcache-admin now provides cacher, coverager and diagnosis
- run unit tests provided by upstream

* Sat Oct 27 2012 Remi Collet <remi@fedoraproject.org> - 2.0.1-4
- drop php prefix from sub packages
- clean EL-5 stuff

* Fri Sep 21 2012 Remi Collet <remi@fedoraproject.org> - 2.0.1-3
- prepare for review with EL-5 stuff

* Fri Sep 21 2012 Remi Collet <remi@fedoraproject.org> - 2.0.1-2
- add admin and coverager sub-package

* Sun Sep  9 2012 Remi Collet <remi@fedoraproject.org> - 2.0.1-1
- initial package

