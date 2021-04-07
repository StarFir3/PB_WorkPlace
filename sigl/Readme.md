
## Image

```
<Event MSec=   "295.1727" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID" ImageBase="0x00400000" ImageSize="0x003D2000" TimeDateStamp="0x5682FC79" OriginalFileName="ccsetup574.exe"/>
<Event MSec=   "295.1727" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID/None"/>
<Event MSec=   "295.1727" PID="3432" PName="ccsetup574" TID="3572" EventName="Image/Load" ImageBase="0x00400000" ImageSize="0x003D2000" ImageChecksum="30,519,123" TimeDateStamp="1,451,424,889" DefaultBase="0x00400000" FileName="C:\Users\User\Downloads\ccsetup574.exe"/>

<Event MSec=   "295.1836" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID" ImageBase="0x76DE0000" ImageSize="0x00142000" TimeDateStamp="0x5C6E21EB" OriginalFileName="ntdll.dll"/>
<Event MSec=   "295.1836" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID/DbgID_RSDS" ImageBase="0x76DE0000" GuidSig="503f56f7-bff6-43f9-99c6-1ae66c3af2a6" Age="2" PdbFileName="ntdll.pdb"/>
<Event MSec=   "295.1836" PID="3432" PName="ccsetup574" TID="3572" EventName="Image/Load" ImageBase="0x76DE0000" ImageSize="0x00142000" ImageChecksum="1,331,219" TimeDateStamp="1,550,721,515" DefaultBase="0x76DE0000" FileName="C:\Windows\System32\ntdll.dll"/>

<Event MSec=  "5663.8470" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/QueryInfo" FileName="C:\Windows\System32\cfgmgr32.dll" IrpPtr="0x84A4FD94" FileObject="0x84FFFF80" FileKey="0x934AED78" ExtraInfo="0x00000000" InfoClass="9"/>
<Event MSec=  "5663.8493" PID="3432" PName="ccsetup574" TID=  "-1" EventName="ImageID" ImageBase="0x74F50000" ImageSize="0x00027000" TimeDateStamp="0x4CE7B787" OriginalFileName="CFGMGR32.DLL"/>
<Event MSec=  "5663.8493" PID="3432" PName="ccsetup574" TID=  "-1" EventName="ImageID/DbgID_RSDS" ImageBase="0x74F50000" GuidSig="93b1a0a8-2f11-4743-af9a-abb1a1738246" Age="2" PdbFileName="cfgmgr32.pdb"/>
<Event MSec=  "5663.8493" PID="3432" PName="ccsetup574" TID=  "-1" EventName="Image/Unload" ImageBase="0x74F50000" ImageSize="0x00027000" ImageChecksum="175,164" TimeDateStamp="1,290,254,215" DefaultBase="0x74F50000" FileName="C:\Windows\System32\cfgmgr32.dll"/>

```

Image events correspond to image (also known as module) files getting loaded and unloaded into process address space. There are four types of Image events: Load, Unload, DCStart and DCEnd. These events do not directly correlate to LoadLibrary calls, however. If a DLL is already loaded in the process, subsequent LoadLibrary calls for the same DLL simply increment the count of module references but will not map the module again. Like the DCStart and DCEnd types of Process and Thread events, Image DCStart and DCEnd are used to enumerate loaded modules of already running processes. Image events allow for the tracking of loaded modules and the mapping of addresses within a process.

## FileIO

### Create

[FileIO/Create](https://docs.microsoft.com/en-us/windows/win32/etw/fileio-create)

```
<Event MSec=   "295.2051" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84C6BC38" CreateOptions="FILE_SYNCHRONOUS_IO_NONALERT" FileAttributes="0" ShareAccess="None" FileName="C:\Windows\Prefetch\CCSETUP574.EXE-60A955CA.pf"/>
<Event MSec=   "295.3778" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84C6BC38" CreateOptions="FILE_DIRECTORY_FILE, FILE_SYNCHRONOUS_IO_NONALERT" FileAttributes="0" ShareAccess="ReadWrite" FileName="C:\Users\User\Downloads\PerfView\"/>
```

#### Create parameters

- CreateOptions : Values passed in the CreateOptions and CreateDispositions parameters to the [NtCreateFile](https://docs.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile) function.
- ShareAccess: The type of share access that the caller would like to use in the file, as zero, or as one or a combination.
- NTCreateFile contains CreateDisposition which specifies what to do, depending on whether the file already exists.

Pattern: Create --> QueryInfo --> CleanUp --> Close

```
<Event MSec=   "298.2751" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84A67F18" CreateOptions="NONE" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Windows\system32\IMM32.DLL"/>
<Event MSec=   "298.2964" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/QueryInfo" FileName="C:\Windows\System32\imm32.dll" IrpPtr="0x84D5D07C" FileObject="0x84A67F18" FileKey="0x93437D78" ExtraInfo="0x00000000" InfoClass="4"/>
<Event MSec=   "298.2993" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x84A67F18" FileKey="0x93437D78" FileName="C:\Windows\System32\imm32.dll"/>
<Event MSec=   "298.3084" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x84A67F18" FileKey="0x93437D78" FileName="C:\Windows\System32\imm32.dll"/>
```

Another Pattern: Create --> FSControl --> DirEnum --> Cleanup --> Close

```
<Event MSec=   "304.6256" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x85029088" CreateOptions="FILE_SYNCHRONOUS_IO_NONALERT" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\"/>
<Event MSec=   "304.6453" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/FSControl" FileName="C:\" IrpPtr="0x84D5D07C" FileObject="0x85029088" FileKey="0x8AE90D08" ExtraInfo="0x00000000" InfoClass="1,311,212"/>
<Event MSec=   "304.6506" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/DirEnum" FileName="Users" IrpPtr="0x84D5D07C" FileObject="0x85029088" FileKey="0x8AE90D08" DirectoryName="C:\" Length="632" InfoClass="37" FileIndex="0"/>
<Event MSec=   "304.6642" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x85029088" FileKey="0x8AE90D08" FileName="C:\"/>
<Event MSec=   "304.6709" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x85029088" FileKey="0x8AE90D08" FileName="C:\"/>
```

- [QueryInfo](https://docs.microsoft.com/en-us/windows/win32/etw/fileio-info) : Set information and query information events indicate that the file attributes were set or queried. A file system control (FSControl)(I/O Control Codes) event is recorded when a [FSCTL](https://social.technet.microsoft.com/wiki/contents/articles/24653.decoding-io-control-codes-ioctl-fsctl-and-deviceiocodes-with-table-of-known-values.aspx) command is issued.
- [Clean up event](https://docs.microsoft.com/en-us/windows/win32/etw/fileio): The event is generated when the last handle to the file is released.
- Close event: The event is generated when the file object is freed.



Read

```
<Event MSec=   "306.9934" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" CreateOptions="NONE" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.0075" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/QueryInfo" FileName="C:\Users\User\Desktop\desktop.ini" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" ExtraInfo="0x00000000" InfoClass="34"/>
<Event MSec=   "307.0098" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.0161" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" FileName="C:\Users\User\Desktop\desktop.ini"/>

<Event MSec=   "307.0417" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" CreateOptions="FILE_SYNCHRONOUS_IO_NONALERT, FILE_NON_DIRECTORY_FILE" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.0573" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/QueryInfo" FileName="C:\Users\User\Desktop\desktop.ini" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" ExtraInfo="0x00000000" InfoClass="5"/>
<Event MSec=   "307.0640" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\Desktop\desktop.ini" Offset="0" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" IoSize="282" IoFlags="395,520"/>
<Event MSec=   "307.0860" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x84A65F18" FileKey="0x9C54D5E8" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.1069" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x859B55B8" CreateOptions="FILE_SYNCHRONOUS_IO_NONALERT, FILE_NON_DIRECTORY_FILE" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.1219" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/QueryInfo" FileName="C:\Users\User\Desktop\desktop.ini" IrpPtr="0x84D5D07C" FileObject="0x859B55B8" FileKey="0x9C54D5E8" ExtraInfo="0x00000000" InfoClass="5"/>
<Event MSec=   "307.1287" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\Desktop\desktop.ini" Offset="0" IrpPtr="0x84D5D07C" FileObject="0x859B55B8" FileKey="0x9C54D5E8" IoSize="282" IoFlags="395,520"/>
<Event MSec=   "307.1410" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x859B55B8" FileKey="0x9C54D5E8" FileName="C:\Users\User\Desktop\desktop.ini"/>
<Event MSec=   "307.1470" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x859B55B8" FileKey="0x9C54D5E8" FileName="C:\Users\User\Desktop\desktop.ini"/>
```

Write
```
<Event MSec=  "5451.5737" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" CreateOptions="NONE" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll"/>
<Event MSec=  "5451.5855" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" CreateOptions="FILE_SYNCHRONOUS_IO_NONALERT, FILE_NON_DIRECTORY_FILE" FileAttributes="0" ShareAccess="Read" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll"/>
<Event MSec=  "5451.6588" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,286,858" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="4" IoFlags="0"/>
<Event MSec=  "5451.6631" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,286,862" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.6704" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="0" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="395,776"/>
<Event MSec=  "5451.7194" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,303,246" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7247" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="16,384" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7269" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="16,384" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="395,776"/>
<Event MSec=  "5451.7475" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,319,630" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7521" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="32,768" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7577" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,336,014" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7620" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="49,152" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7639" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="49,152" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="395,776"/>
<Event MSec=  "5451.7838" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,352,398" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7885" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="65,536" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7942" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,368,782" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.7986" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="81,920" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="16,384" IoFlags="0"/>
<Event MSec=  "5451.8049" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Read" FileName="C:\Users\User\AppData\Local\Temp\nsg251B.tmp" Offset="60,385,166" IrpPtr="0x84D5D07C" FileObject="0x84CB66E0" FileKey="0xBB855D20" IoSize="12,624" IoFlags="0"/>
<Event MSec=  "5451.8089" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Write" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" Offset="98,304" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" IoSize="12,624" IoFlags="0"/>
<Event MSec=  "5451.8164" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/SetInfo" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" ExtraInfo="0x00000000" InfoClass="4"/>
<Event MSec=  "5451.8390" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll"/>
<Event MSec=  "5451.8568" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA3657CF8" FileName="C:\Program Files\CCleaner\Lang\lang-1025.dll"/>
```

FileCheck before Write
```
<Event MSec=  "5451.5498" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Create" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" CreateOptions="FILE_DIRECTORY_FILE, FILE_SYNCHRONOUS_IO_NONALERT" FileAttributes="0" ShareAccess="ReadWrite, Delete" FileName="C:\Program Files\CCleaner\Lang\"/>
<Event MSec=  "5451.5574" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/DirEnum" FileName="lang-1025.dll" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA36A59D0" DirectoryName="C:\Program Files\CCleaner\Lang" Length="616" InfoClass="3" FileIndex="0"/>
<Event MSec=  "5451.5622" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Cleanup" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA36A59D0" FileName="C:\Program Files\CCleaner\Lang"/>
<Event MSec=  "5451.5657" PID="3432" PName="ccsetup574" TID="3572" EventName="FileIO/Close" IrpPtr="0x84D5D07C" FileObject="0x84D5DF80" FileKey="0xA36A59D0" FileName="C:\Program Files\CCleaner\Lang"/>
```

DLL Load

```
<Event MSec=  "5483.7104" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID" ImageBase="0x73660000" ImageSize="0x00009000" TimeDateStamp="0x4A5BDA0C" OriginalFileName="LINKINFO.DLL"/>
<Event MSec=  "5483.7104" PID="3432" PName="ccsetup574" TID="3572" EventName="ImageID/DbgID_RSDS" ImageBase="0x73660000" GuidSig="c59792ac-f0f3-4ec8-9b92-2f50152d26f7" Age="2" PdbFileName="linkinfo.pdb"/>
<Event MSec=  "5483.7104" PID="3432" PName="ccsetup574" TID="3572" EventName="Image/Load" ImageBase="0x73660000" ImageSize="0x00009000" ImageChecksum="57,212" TimeDateStamp="1,247,533,580" DefaultBase="0x73660000" FileName="C:\Windows\System32\linkinfo.dll"/>
```

DLL Unload

```
<Event MSec=  "5663.6050" PID="3432" PName="ccsetup574" TID=  "-1" EventName="ImageID" ImageBase="0x73160000" ImageSize="0x0000F000" TimeDateStamp="0x4CE7B9A0" OriginalFileName="SAMCLI.DLL"/>
<Event MSec=  "5663.6050" PID="3432" PName="ccsetup574" TID=  "-1" EventName="ImageID/DbgID_RSDS" ImageBase="0x73160000" GuidSig="76380d8e-5cfe-4600-901e-6045ed45c981" Age="2" PdbFileName="samcli.pdb"/>
<Event MSec=  "5663.6050" PID="3432" PName="ccsetup574" TID=  "-1" EventName="Image/Unload" ImageBase="0x73160000" ImageSize="0x0000F000" ImageChecksum="59,488" TimeDateStamp="1,290,254,752" DefaultBase="0x73160000" FileName="C:\Windows\System32\samcli.dll"/>
```