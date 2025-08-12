%global package_speccommit ec53f681c8c566260b03e099643d83f05d01edec
%global usver 1.8.19
%global xsver 2
%global xsrel %{xsver}%{?xscount}%{?xshash}
%global       gitname     IPMITOOL
%global       gitversion  1_8_19

Name:         ipmitool
Summary:      Utility for IPMI control
Version:      1.8.19
Release: %{?xsrel}%{?dist}
License:      BSD
URL:          http://ipmitool.sourceforge.net/
Source0: ipmitool-1.8.19.tar.gz
Source1: openipmi-ipmievd.sysconf
Source2: ipmievd.service
Source3: exchange-bmc-os-info.service
Source4: exchange-bmc-os-info.sysconf
Source5: set-bmc-url.sh
Source6: exchange-bmc-os-info
Source7: enterprise-numbers
Patch0: ipmitool-1.8.19-set-kg-key.patch
Patch1: 0004-slowswid.patch
Patch2: 0005-sensor-id-length.patch
Patch3: 0007-check-input.patch


BuildRequires: openssl-devel readline-devel ncurses-devel
%{?systemd_requires}
BuildRequires: systemd
# bootstrap
BuildRequires: automake autoconf libtool
Obsoletes: OpenIPMI-tools < 2.0.14-3
Provides: OpenIPMI-tools = 2.0.14-3


%description
This package contains a utility for interfacing with devices that support
the Intelligent Platform Management Interface specification.  IPMI is
an open standard for machine health, inventory, and remote power control.

This utility can communicate with IPMI-enabled devices through either a
kernel driver such as OpenIPMI or over the RMCP LAN protocol defined in
the IPMI specification.  IPMIv2 adds support for encrypted LAN
communications and remote Serial-over-LAN functionality.

It provides commands for reading the Sensor Data Repository (SDR) and
displaying sensor values, displaying the contents of the System Event
Log (SEL), printing Field Replaceable Unit (FRU) information, reading and
setting LAN configuration, and chassis power control.


%package -n ipmievd
Requires: ipmitool
%{?systemd_requires}
BuildRequires: systemd
Summary: IPMI event daemon for sending events to syslog
%description -n ipmievd
ipmievd is a daemon which will listen for events from the BMC that are
being  sent to the SEL and also log those messages to syslog.


%package -n bmc-snmp-proxy
Requires: net-snmp
Requires: exchange-bmc-os-info
BuildArch: noarch
Summary: Reconfigure SNMP to include host SNMP agent within BMC
%description -n bmc-snmp-proxy
Given a host with BMC, this package would extend system configuration
of net-snmp to include redirections to BMC based SNMP.


%package -n exchange-bmc-os-info
Requires: hostname
Requires: ipmitool
BuildArch: noarch
%{?systemd_requires}
BuildRequires: systemd
BuildRequires: make

Summary: Let OS and BMC exchange info

%description -n exchange-bmc-os-info
Given a host with BMC, this package would pass the hostname &
OS information to the BMC and also capture the BMC ip info
for the host OS to use.


%prep
%autosetup -n %{name}-%{gitname}_%{gitversion} -p1

for f in AUTHORS ChangeLog; do
    iconv -f iso-8859-1 -t utf8 < ${f} > ${f}.utf8
    mv ${f}.utf8 ${f}
done

%build
# --disable-dependency-tracking speeds up the build
# --enable-file-security adds some security checks
# --disable-intf-free disables FreeIPMI support - we don't want to depend on
#   FreeIPMI libraries, FreeIPMI has its own ipmitoool-like utility.

# begin: release auto-tools
# Used to be needed by aarch64 support, now only cxoem patch makefiles are left.
aclocal
libtoolize --automake --copy
autoheader
automake --foreign --add-missing --copy
aclocal
autoconf
automake --foreign
# end: release auto-tools

install -Dm 644 %{SOURCE7} .
%configure --disable-dependency-tracking --enable-file-security --disable-intf-free --enable-intf-usb
make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

install -Dpm 644 %{SOURCE2} %{buildroot}%{_unitdir}/ipmievd.service
install -Dpm 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/sysconfig/ipmievd
install -Dm 644 %{SOURCE3} %{buildroot}%{_unitdir}/exchange-bmc-os-info.service
install -Dm 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/exchange-bmc-os-info
install -Dm 644 %{SOURCE5} %{buildroot}%{_sysconfdir}/profile.d/set-bmc-url.sh
install -Dm 755 %{SOURCE6} %{buildroot}%{_libexecdir}/exchange-bmc-os-info


install -Dm 644 contrib/bmc-snmp-proxy.sysconf %{buildroot}%{_sysconfdir}/sysconfig/bmc-snmp-proxy
install -Dm 644 contrib/bmc-snmp-proxy.service %{buildroot}%{_unitdir}/bmc-snmp-proxy.service
install -Dm 755 contrib/bmc-snmp-proxy         %{buildroot}%{_libexecdir}/bmc-snmp-proxy

%post -n ipmievd
%systemd_post ipmievd.service

%preun -n ipmievd
%systemd_preun ipmievd.service

%postun -n ipmievd
%systemd_postun_with_restart ipmievd.service

%post -n exchange-bmc-os-info
%systemd_post exchange-bmc-os-info.service

%preun -n exchange-bmc-os-info
%systemd_preun exchange-bmc-os-info.service

%postun -n exchange-bmc-os-info
%systemd_postun_with_restart exchange-bmc-os-info.service


%triggerun -- ipmievd < 1.8.11-7
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply ipmievd
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save ipmievd >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del ipmievd >/dev/null 2>&1 || :
/bin/systemctl try-restart ipmievd.service >/dev/null 2>&1 || :

%files
%{_bindir}/ipmitool
%{_mandir}/man1/ipmitool.1*
%doc %{_datadir}/doc/ipmitool
%{_datadir}/ipmitool
%{_datadir}/misc/enterprise-numbers

%files -n ipmievd
%config(noreplace) %{_sysconfdir}/sysconfig/ipmievd
%{_unitdir}/ipmievd.service
%{_sbindir}/ipmievd
%{_mandir}/man8/ipmievd.8*

%files -n exchange-bmc-os-info
%config(noreplace) %{_sysconfdir}/sysconfig/exchange-bmc-os-info
%{_sysconfdir}/profile.d/set-bmc-url.sh
%{_unitdir}/exchange-bmc-os-info.service
%{_libexecdir}/exchange-bmc-os-info

%files -n bmc-snmp-proxy
%config(noreplace) %{_sysconfdir}/sysconfig/bmc-snmp-proxy
%{_unitdir}/bmc-snmp-proxy.service
%{_libexecdir}/bmc-snmp-proxy

%changelog
* Wed Nov 20 2024 Stephen Cheng <stephen.cheng@cloud.com> - 1.8.19-2
- CP-49464: Rebuild with updated dependencies to remove compat packages

* Thu Dec 21 2023 Lin Liu <lin.liu@citrix.com> - 1.8.19-1
- First imported release

