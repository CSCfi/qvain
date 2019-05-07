# -wvh- spec file for Qvain
#
#       This builds qvain-api and qvain-js packages:
#         - the API backend depends on postgresql 9.6, redis and systemd;
#         - the Javascript backend depends on nothing.
#
#       The packages are built from their respective git repos without the
#       common "create tarball" step in between.
#
#       On upgrade, qvain-api will restart the service if it is running.
#

%global debug_package    %{nil}
%global provider         github.com
%global project          CSCfi

# convert semver with major.minor.patch to major.minor
%define semMajorMinor()  %(echo "%1" | sed 's/^[^0-9]*\\([0-9]*\\)\\.\\([0-9]*\\).*$/\\1.\\2/')
# convert git tag to semver
%define versionPart()    %(echo "%1" | sed -e 's/^v//' -e 's/-.*//')
# convert extra data in git tag to release field
%define releasePart()    %(echo "%1" | sed -e 's/^[^-]*//;tx;d;:x;s/-/_/g;s/^[^a-z0-9]//;')
# remove leading 'v' and change dashes to underscores in versions
%define validVersion()   %(echo "%1" | sed -e 's/^v//' -e 's/-/_/g')

# global package version = major.minor (no patch) of backend
%global _version         %versionPart %{apiVersion}
%global version          %{?_version:%semMajorMinor %{_version}}%{!?_version:0.0.0}

%global api_repo         qvain-api
%global api_semver       %{?apiVersion:%versionPart %{apiVersion}}%{!?apiVersion:%{version}}
%global api_version      %{?apiVersion:%validVersion %{apiVersion}}%{!?apiVersion:%{version}}
%global api_commit       %{?apiCommit}
%global api_shortcommit  %(c=%{api_commit}; echo ${c:0:7})
%global api_release      %{?apiBuild}%{!?apiBuild:1}
%global import_path      %{provider}/%{project}/%{api_repo}

%global js_repo          qvain-js
%global js_version       %{?jsVersion:%validVersion %{jsVersion}}%{!?jsVersion:%{version}}
%global js_commit        %{?jsCommit}
%global js_shortcommit   %(c=%{js_commit}; echo %{c:0:7})
%global js_release       %{?jsBuild}%{!?jsBuild:1}
%global js_url           %{provider}/%{project}/%{js_repo}

%global app_user         qvain
%global app_group        qvain
%global app_path         /srv/qvain

%global app_description  Qvain is the dataset description service for the Fairdata project.

# commit: git rev-parse --short HEAD 2>/dev/null
# tag:    git describe --always 2>/dev/null
# repo:   git ls-remote --get-url 2>/dev/null
# user:   git config user.name
# email:  git config user.email

Name:       qvain
Version:    %{version}
Release:    1%{?dist}
Summary:    Qvain backend service for the Fairdata project
License:    GPLv3+
Source:     https://%{import_path}/archive/%{api_commit}/%{api_repo}-%{api_shortcommit}.tar.gz
URL:        https://%{import_path}
Provides:   qvain = %{version}
#Provides:   qvain = %{version}-%{release}
#%if 0%{?centos} || 0%{?fedora}
#ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm} aarch64 ppc64le s390x}
#%else
#ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:x86_64 %{arm} aarch64 ppc64le s390x}
#%endif
Requires(pre): shadow-utils

%description
This package contains Qvain, the dataset description service for the Fairdata project.

%package api
Summary:          Qvain backend service
URL:              https://%{import_path}
Version:          %{api_version}
Release:          %{api_release}%{?dist}
#Provides:         %{api_repo} = %{api_version}-%{release}
Provides:         %{api_repo} = %{api_semver}
#BuildRequires:    golang >= 1.9.0
BuildRequires:    systemd
#Requires:         %{js_repo} = %{version}-%{release}
Requires:         postgresql >= 9.6, postgresql-server >= 9.6, redis > 3.2
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
%description api
%{app_description}

This package contains the backend service binaries.

%package js
Summary:    Qvain frontend application
URL:        https://%{js_url}
Version:    %{js_version}
Release:    %{js_release}%{?dist}
#Requires:   %{api_repo} = %{api_version}-%{release}
Requires:   %{api_repo} = %{api_semver}
BuildArch:  noarch
%description js
%{app_description}

This package contains the Javascript frontend code.


%prep

%build

%install
mkdir -p %{buildroot}/%{app_path}/{bin,schema,doc,log,web}
cp -a %{app_path}/bin/* %{buildroot}/%{app_path}/bin/
cp -a %{app_path}/schema/* %{buildroot}/%{app_path}/schema/
cp -a %{app_path}/doc/* %{buildroot}/%{app_path}/doc/
cp -a %{app_path}/web/* %{buildroot}/%{app_path}/web/

%clean

%files api
%defattr(-,root,root)
%{app_path}/bin/*
%{app_path}/schema/*
%{app_path}/doc/*
%attr(-,%{app_user},%{app_group}) %{app_path}/log/

%files js
%attr(-,%{app_user},%{app_group}) %{app_path}/web/

%pre
getent group %{app_group} >/dev/null || groupadd -r %{app_group}
getent passwd %{app_user} >/dev/null || useradd -r -g %{app_group} -d %{app_home} -s /sbin/nologin -c "Qvain service user" %{app_user}
exit 0

# https://github.com/systemd/systemd/blob/master/src/core/macros.systemd.in

%post
if [ $1 -eq 1 ]; then
	# initial installation
	systemctl --no-reload preset %{?*} &>/dev/null || :

%preun
if [ $1 -eq 0 ]; then
	# removal
	systemctl --no-reload disable --now %{?*} &>/dev/null || : \
fi

%postun
if [ $1 -eq 0 ]; then
	# uninstall
fi
if [ $1 -eq 1 ]; then
        # upgrade
        systemctl try-restart %{?*} &>/dev/null || :
fi


%changelog
* Tue Apr 9 2019 %(echo 'Jbhgre Ina Urzry <jbhgre.ina.urzry@uryfvaxv.sv>' | tr 'A-Za-z' 'N-ZA-Mn-za-m') 0.4.0
- make binary-only spec file that packages Docker output

* Fri Jun 22 2018 %(echo 'Jbhgre Ina Urzry <jbhgre.ina.urzry@uryfvaxv.sv>' | tr 'A-Za-z' 'N-ZA-Mn-za-m') 0.3.0
- add frontend package
- add systemd logic

* Fri Jun 22 2018 %(echo 'Jbhgre Ina Urzry <jbhgre.ina.urzry@uryfvaxv.sv>' | tr 'A-Za-z' 'N-ZA-Mn-za-m') 0.2.0
- build from git

* Wed Jun 13 2018 %(echo 'Jbhgre Ina Urzry <jbhgre.ina.urzry@uryfvaxv.sv>' | tr 'A-Za-z' 'N-ZA-Mn-za-m') 0.1.0
- initial version
