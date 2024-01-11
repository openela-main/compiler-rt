%global compiler_rt_version 15.0.7
#global rc_ver 2
%global crt_srcdir compiler-rt-%{compiler_rt_version}%{?rc_ver:rc%{rc_ver}}.src

# see https://sourceware.org/bugzilla/show_bug.cgi?id=25271
%global optflags %(echo %{optflags} -D_DEFAULT_SOURCE)

# see https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93615
%global optflags %(echo %{optflags} -Dasm=__asm__)

Name:		compiler-rt
Version:	%{compiler_rt_version}%{?rc_ver:~rc%{rc_ver}}
Release:	1%{?dist}
Summary:	LLVM "compiler-rt" runtime libraries

License:	NCSA or MIT
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{compiler_rt_version}%{?rc_ver:-rc%{rc_ver}}/%{crt_srcdir}.tar.xz
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{compiler_rt_version}%{?rc_ver:-rc%{rc_ver}}/%{crt_srcdir}.tar.xz.sig
Source2:	release-keys.asc

Patch0:		add-llvm-cmake-package.patch

# RHEL-specific patches
Patch100:	0001-Drop-fno-stack-protector-from-the-compiler-flags.patch
Patch101:	fix-page-size-constant.patch

BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	cmake
BuildRequires:	ninja-build
BuildRequires:	python3
# We need python3-devel for pathfix.py.
BuildRequires:	python3-devel
BuildRequires:	llvm-devel = %{version}

# For gpg source verification
BuildRequires:	gnupg2

Requires: clang-resource-filesystem%{?isa} = %{version}

%description
The compiler-rt project is a part of the LLVM project. It provides
implementation of the low-level target-specific hooks required by
code generation, sanitizer runtimes and profiling library for code
instrumentation, and Blocks C language extension.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup -n %{crt_srcdir} -p2

%py3_shebang_fix lib/hwasan/scripts/hwasan_symbolize

%build
mkdir -p %{_vpath_builddir}
cd %{_vpath_builddir}

%cmake .. -GNinja \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DLLVM_CONFIG_PATH:FILEPATH=%{_bindir}/llvm-config-%{__isa_bits} \
	\
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
	-DCOMPILER_RT_INCLUDE_TESTS:BOOL=OFF # could be on?

%cmake_build

%install

cd %{_vpath_builddir}
%cmake_install

# move blacklist/abilist files to where clang expect them
mkdir -p %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/share
mv -v %{buildroot}%{_datadir}/*list.txt  %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/share/

# move sanitizer libs to better place
%global libclang_rt_installdir lib/linux
mkdir -p %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/lib
mv -v %{buildroot}%{_prefix}/%{libclang_rt_installdir}/*clang_rt* %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/lib
mkdir -p %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/lib/linux/
pushd %{buildroot}%{_libdir}/clang/%{compiler_rt_version}/lib
for i in *.a *.so
do
	ln -s ../$i linux/$i
done

# multilib support: also create symlink from lib to lib64, fixes rhbz#1678240
# the symlinks will be dangling if the 32 bits version is not installed, but that should be fine
%ifarch x86_64

mkdir -p %{buildroot}/%{_exec_prefix}/lib/clang/%{compiler_rt_version}/lib/linux
for i in *.a *.so
do
	target=`echo "$i" | sed -e 's/x86_64/i386/'`
	ln -s ../../../../../lib/clang/%{compiler_rt_version}/lib/$target ../../../../%{_lib}/clang/%{compiler_rt_version}/lib/linux/
done

%endif

popd

%check

#%%cmake_build --target check-compiler-rt

%files
%license LICENSE.TXT
%{_includedir}/*
%{_libdir}/clang/%{compiler_rt_version}/lib/*
%{_libdir}/clang/%{compiler_rt_version}/share/*
%ifarch x86_64 aarch64
%{_bindir}/hwasan_symbolize
%endif

%changelog
* Thu Jan 19 2023 Tom Stellard <tstellar@redhat.com> - 15.0.7-1
- Update to LLVM 15.0.7

* Tue Sep 06 2022 Nikita Popov <npopov@redhat.com> - 15.0.0-1
- Update to LLVM 15.0.0

* Tue Jun 28 2022 Tom Stellard <tstellar@redhat.com> - 14.0.6-1
- 14.0.6 Release

* Wed May 25 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-3
- Fix page size constant size on aarch64 and ppc64le

* Fri Apr 29 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-2
- Remove llvm-cmake-devel BR

* Thu Apr 07 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-1
- Update to 14.0.0

* Thu Feb 03 2022 Tom Stellard <tstellar@redhat.com> - 13.0.1-1
- 13.0.1 Release

* Fri Oct 15 2021 Tom Stellard <tstellar@redhat.com> - 13.0.0-1
- 13.0.0 Release

* Fri Jul 16 2021 sguelton@redhat.com - 12.0.1-1
- 12.0.1 release

* Tue May 25 2021 sguelton@redhat.com - 12.0.0-2
- Backport several compatibility patches

* Thu May 6 2021 sguelton@redhat.com - 12.0.0-1
- 12.0.0 release

* Thu Oct 29 2020 sguelton@redhat.com - 11.0.0-1
- 11.0.0 final release

* Mon Sep 21 2020 sguelton@redhat.com - 11.0.0-0.1.rc2
- 11.0.0-rc2 Release

* Fri Jul 24 2020 sguelton@redhat.com - 10.0.1-1
- 10.0.1 release

* Mon Jun 15 2020 sguelton@redhat.com - 10.0.0-2
- Fix msan compilation warnings, see rhbz#1841165

* Wed Apr 8 2020 sguelton@redhat.com - 10.0.0-1
- 10.0.0 final

* Mon Jan 06 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-2
- Update fno-stack-protector patch to apply with -p2

* Fri Dec 20 2019 Tom Stellard <tstellar@redhat.com> - 9.0.1-1
- 9.0.1 Release

* Fri Sep 27 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-1
- 9.0.0 Release

* Thu Aug 1 2019 sguelton@redhat.com - 8.0.1-1
- 8.0.1 release

* Thu Jul 4 2019 sguelton@redhat.com - 8.0.1-0.2.rc2
- Fix rhbz#1678240

* Thu Jun 13 2019 sguelton@redhat.com - 8.0.1-0.1.rc2
- 8.0.1rc2 Release

* Wed Apr 17 2019 sguelton@redhat.com - 8.0.0-1
- 8.0.0 Release 

* Fri Dec 14 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-1
- 7.0.1 Release 

* Mon Dec 10 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.1.rc3
- 7.0.1-rc3 Release 

* Tue Nov 27 2018 Tom Stellard <tstellar@redhat.com> - 7.0.0-1
- 7.0.0 Release 

* Tue Oct 02 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-5
- Use python3 for build scripts

* Mon Oct 01 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-4
- Drop scl macros

* Thu Sep 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-3
- Drop -fno-stack-protector flag

* Thu Sep 06 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-2
- Explicitly BuildRequire: /usr/bin/python3

* Wed Jul 11 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-1
- 6.0.1 Release

* Tue Jan 09 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-1
- 5.0.1 Release

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- 4.0.1 Release

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Build for llvm-toolset-7 rename

* Thu May 18 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Fix disabling debug on s390(x)

* Tue Mar 14 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- compiler-rt 4.0.0 Final Release

* Thu Mar 02 2017 Dave Airlie <airlied@redhat.com> - 3.9.1-1
- compiler-rt 3.9.1

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 21 2016 Dan Horák <dan[at]danny.cz> - 3.9.0-3
- disable debuginfo on s390(x)

* Wed Nov 02 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-2
- build for new arches.

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- compiler-rt 3.9.0 final release

* Mon May  2 2016 Tom Callaway <spot@fedoraproject.org> 3.8.0-2
- make symlinks to where the linker thinks these libs are

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- compiler-rt 3.8.0 final release

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- compiler-rt 3.8.0rc3

* Thu Feb 18 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.1
- compiler-rt 3.8.0rc2

* Fri Feb 05 2016 Dave Airlie <airlied@redhat.com> 3.7.1-3
- fix compiler-rt paths - from rwindz0@gmail.com - #1304605

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
