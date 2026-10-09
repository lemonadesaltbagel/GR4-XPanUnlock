#!/usr/bin/env python3
"""GR4-XPanUnlock: an XPan (65:24) aspect ratio for the RICOH GR IV (firmware 1.11).

Adds XPan as a fifth aspect ratio next to 16:9. In live view, XPan, 16:9,
4:3 and 1:1 show the whole frame with the area outside the crop dimmed. Turns
the official RICOH firmware file you downloaded yourself into the XPan
version. A file is written only if every check passes.

Usage
  python3 gr4_xpanunlock.py patch  OFFICIAL_fwdc248b.bin  [-o OUTPUT_DIR]
  python3 gr4_xpanunlock.py check  ANY_fwdc248b.bin

Python 3.8 or newer, no extra packages.
"""
import argparse
import base64
import hashlib
import struct
import sys
import zlib
from pathlib import Path

VERSION = '2.0.0'

OFFICIAL_SHA256 = 'a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f'
OFFICIAL_BYTES = 38648776

UNLOCKED_SHA256 = 'aa9ac5dbb05d0e362019b78c678ac322fe9b6786d980cafe1846bf191f739cb0'

# Other known GR IV 1.11 builds that this tool should not be fed (identified by `check`).
OTHER_KNOWN = {
    '4c04b48c65897f2edd028df0f5e04666ca241488c81502bae0f34e040ee454eb': 'GR4-MonoUnlock 1.0.0 (monochrome looks unlocked)',
    'fa2c67d1b67e16675a0c75b98d58c519b803f049a00e40e34103e54ca9a6a6c7': 'GR4-XPanUnlock 1.0.0 (16:9 replaced by XPan, letterboxed live view)',
    '4534d44297b69bb6d305bac2ad62fef98b0caf7a6558d6da36c049dbb88f80c8': 'GR4-XPanUnlock 1.1.0 (16:9 replaced by XPan)',
}

# (payload offset, original bytes, new bytes, what it does)
# All changes keep every size and address unchanged. New routines are written in place over code the camera
# never runs, and they only read from the firmware, never write to it.
CHANGES = [
    (0x01a6e18, 'eaffff0a', 'e0011d0a',
     'live view: whole frame with the crop dimmed'),
    (0x01a6e68, '9ea50feb', 'c2011deb',
     'live view: whole frame with the crop dimmed'),
    (0x01d1e5c, '0400a0e3', '0500a0e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01d20c0, '157816eb', '52041beb',
     'image-size readout for XPan'),
    (0x01d2c98, '34300be3db3345e3', 'f0350fe38c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01d2f7c, '34300be3db3345e3', 'f0350fe38c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01d602c, '34300be3', 'f0350fe3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01d6034, 'db3345e3', '8c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01d8880, '255e16eb', '62ea1aeb',
     'image-size readout for XPan'),
    (0x01e6fa8, '0400a0e3', '0500a0e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01e89f8, '34300be3', 'f0350fe3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01e8a00, 'db3345e3', '8c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01e8ad0, '911d16eb', 'cea91aeb',
     'image-size readout for XPan'),
    (0x01eac98, '34300be3db3345e3', 'f0350fe38c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x01ec5b0, '34300be3db3345e3', 'f0350fe38c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x022e01c, '030053e3', 'ce9419ea',
     'Crop: XPan frames'),
    (0x02558c4, '963200e3', '973200e3',
     'XPan icon'),
    (0x02558d0, '8fc606eb', '6ef618eb',
     'XPan icon'),
    (0x02558e4, '8ac606eb', '69f618eb',
     'XPan icon'),
    (0x025611c, '962200e3', '972200e3',
     'XPan icon'),
    (0x02561e4, '4ac406eb', '30f418eb',
     'XPan icon'),
    (0x0272b3c, '34300be3db3345e3', 'f0350fe38c3345e3',
     'aspect menu: XPan as a fifth ratio'),
    (0x0272b74, '0000a003', '0400a003',
     'aspect menu: XPan as a fifth ratio'),
    (0x03834a8, 'a0b73653', 'bcb73653',
     'RAW Development: XPan choice'),
    (0x03834d4, '0400a0e3', '0500a0e3',
     'RAW Development: XPan choice'),
    (0x0383628, '44b93653', '1cb68753',
     'RAW Development: XPan choice'),
    (0x038364c, '44b93653', '1cb68753',
     'RAW Development: XPan choice'),
    (0x0383674, '80380be3db3345e3', 'fc360be3873345e3',
     'RAW Development: XPan choice'),
    (0x03855b8, 'd8350be3db3345e3', '04370be3873345e3',
     'RAW Development: XPan choice'),
    (0x03855f0, '80380be3db3345e3', 'fc360be3873345e3',
     'RAW Development: XPan choice'),
    (0x038cda8, '040051e3', '581914ea',
     'RAW Development: XPan choice'),
    (0x03978e4, '0000a013', '09010013',
     'aspect menu: XPan as a fifth ratio'),
    (0x0399178, '01208213000052e30000a013f000a003', '97020013f000a003000052e30000a013',
     'aspect menu: XPan as a fifth ratio'),
    (0x03b648c, '28380de3d01803e3db3345e3e0280ce300308de5', '740100e30a3da0e36c20a0e35010a0e3eaffffea',
     'focus area: limited to the picture'),
    (0x03b6760, '50380de3d01803e3db3345e3e0280ce300308de5', '0500a0e1231ea0e3422fa0e3c12d15ebafffffea',
     'focus area: limited to the picture'),
    (0x03b976c, '2d00000a', '0a6613ea',
     'playback: recognise XPan pictures'),
    (0x03ba608, '0000a0e3', '586313ea',
     'Crop: XPan sizes'),
    (0x03f43f0, 'c43f01e3', '08370be3',
     'Crop: XPan frames'),
    (0x03f43f8, '003545e3', '873345e3',
     'Crop: XPan frames'),
    (0x03f473c, '030051e3', '040051e3',
     'Crop: XPan frames'),
    (0x03f47c4, 'c43f01e3003545e3', '08370be3873345e3',
     'Crop: XPan frames'),
    (0x03f484c, '0450a0e3', '0550a0e3',
     'Crop: XPan frames'),
    (0x03f4854, '030053e3', 'b97a12ea',
     'Crop: XPan frames'),
    (0x03f4864, '60cb3d53', '44b68753',
     'Crop: XPan frames'),
    (0x03f491c, '030050e3', '040050e3',
     'Crop: XPan frames'),
    (0x03f4948, '030053e3', '040053e3',
     'Crop: XPan frames'),
    (0x03f4978, 'c43f01e3003545e3', '08370be3873345e3',
     'Crop: XPan frames'),
    (0x03f4d60, 'c47f01e3', '08770be3',
     'Crop: XPan frames'),
    (0x03f4d6c, '007545e3', '877345e3',
     'Crop: XPan frames'),
    (0x03f4df4, 'd41f0055', '1cb78753',
     'Crop: XPan frames'),
    (0x03f50f0, 'c4cf01e3', '08c70be3',
     'Crop: XPan frames'),
    (0x03f50f8, '00c545e3', '87c345e3',
     'Crop: XPan frames'),
    (0x03f523c, 'c4ef01e3', '08e70be3',
     'Crop: XPan frames'),
    (0x03f5248, '00e545e3', '87e345e3',
     'Crop: XPan frames'),
    (0x03f5428, 'c43f01e3003545e3', '08370be3873345e3',
     'Crop: XPan frames'),
    (0x0712ebc, 'da27d2e5', '8a0006ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0712f20, 'da27dce5', '790006ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0712fc4, 'da17d1e5', '580006ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x071309c, 'da17d1e5', '2a0006ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x071a4b8, 'da27d3e5', '03e305ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x072399c, 'da17d1e5', 'babd05ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x07239e4, 'da17d1e5', 'b0bd05ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0729154, 'da27d3e5', 'a4a705ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0729314, 'da27dce5', '3ca705ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x077e6c0, '0dc0a0e1', 'd2a205ea',
     'aspect menu: XPan as a fifth ratio'),
    (0x0892ed8,
        '0dc0a0e1bc3904e3f0df2de9353445e304b04ce2028b2ded6cd04de2042090e5'
        '7c300be5003093e5000052e358000be538300be5bd02000a18340fe3fc3345e3'
        '70300be5c9bcffeb3810a0e3fbbcffeb000050e30070a00178700b054202001a'
        'c2bcffeb8110a0e3f4bcffeb000050e30080a0010840a0018102001abbbcffeb'
        '7710a0e3edbcffeb000050e35c02001a0630a0e36c300be50130a0e384300be5'
        'b2bcffeb4010a0e3e4bcffeb000050e364000b054802001aacbcffeb9410a0e3'
        'debcffeb000050e38c000b05fe3ea00368300b053302001a78301be5000054e3'
        '0280a003000053e31702000a1c3087e2fdce87e27330ffe604c08ce25c300be5'
        'fb9e83e27cc0ffe6089089e2063087e260300be558301be50060a0e380c00be5'
        '0620a0e3044093e51630a0e3f40094e5c85094e588000be56c005be5ec1094e5'
        'd8a094e5b080c5e1208085e2be20c5e1b031c5e1b670c5e1b860c5e1bc60c5e1'
        '2800c5e574100be5b4654be1b2654be1ac5401eb085501eb003090e50070a0e1'
        '0610a0e1343093e533ff2fe1003097e552204be200208de50700a0e1087093e5'
        '0610a0e1408ab0ee0620a0e154304be237ff2fe184305be53820a0e3bc055be1'
        '881701e32930c5e51c30a0e3bc31c5e1b83f00e3b422c5e10420a0e380c01be5'
        'b202c5e1c40701e3be31c5e1b824cae174201be5b630cae1e03701e3b2c0cae1'
        'b000cae10400a0e1b410cae10610a0e1b230c2e1b634cae1f1f4ffeb64301be5'
        '0400a0e10010a0e3060053e10630a011ee30a00380300be5092063e08c301be5'
        '0c2082e264701b05ee70a013022083e00360a0e364200be561f5ffeb0400a0e1'
        '0110a0e354f5ffeb0400a0e10010a0e3abf5ffeb0400a0e10010a0e362f5ffeb'
        '0400a0e10010a0e369f5ffeb0710a0e10400a0e1',
        '0030a0e330c801e30c0050e1f03800030020a00350c301e30c0050e120370003'
        '0120a003b0cd00e30c0050e1103500030220a00380c700e30c0050e1c8320003'
        '0320a0031eff2fe1040052e37752011a0dc0a0e130d82de904b04ce200509ce5'
        '0340a0e108d04de200508de50220a0e36e5201ebb000d4e1e0ffffeb000053e3'
        'b030c51114d04be230a89de8040051e39553011a0000a0e36b10a0e3b000c2e1'
        'b010c3e11eff2fe1040051e3bc53011a0000a0e31e10a0e3b000c2e1b010c3e1'
        '1eff2fe1219aec0a09002de9010381e0823082e0830150e000006042a20150e1'
        '0900bde80200a0933080bd98e999eceac2ffffeb000053e30300000a030054e1'
        '0100001a0230a0e1ee9decea0000a0e3879decea03002de9db07d3e5010050e3'
        'da27d3e5020052030420a0030300bde85258faea03002de9db07dce5010050e3'
        'da27dce5020052030420a0030300bde8ba58faea03002de9db07d8e5010050e3'
        'da27d8e5020052030420a0030300bde81d2800ea05002de9db07d1e5010050e3'
        'da47d1e5020054030440a0030500bde8cf2700ea05002de9db07d1e5010050e3'
        'da77d1e5020057030470a0030500bde8632800ea05002de9db07d1e5010050e3'
        'da17d1e5020051030410a0030500bde83c42faea05002de9db07d1e5010050e3'
        'da17d1e5020051030410a0030500bde84642faea03002de9db07d3e5010050e3'
        'da27d3e5020052030420a0030300bde8f31cfaea03002de9db07d2e5010050e3'
        'da27d2e5020052030420a0030300bde86cfff9ea03002de9db07dce5010050e3'
        'da27dce5020052030420a0030300bde87dfff9ea05002de9db07d1e5010050e3'
        'da17d1e5020051030410a0030500bde89efff9ea05002de9db07d1e5010050e3'
        'da17d1e5020051030410a0030500bde8ccfff9ea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0893210,
        'd9f4ffeb6c101be50400a0e1e0f4ffeb88700be50700a0e1e01701e3ebebffeb'
        '7010ffe60400a0e1e3f4ffeb0400a0e13810a0e3fef4ffeb0400a0e11c10a0e3'
        '05f5ffeb0400a0e1881701e3e4f4ffebb81f00e30400a0e1ebf4ffeb64201be5'
        '0810a0e3',
        'c83801e30dc0a0e1fe3345e330d82de90050a0e1001093e52c4080e204b04ce2'
        '0400a0e13e9201eb180595e5040000eb0050a0e10400a0e18e9201eb0500a0e1'
        '30a89de8003090e5da07d3e5020050e31eff2f11db37d3e5010053e30400a003'
        '1eff2fe1',
     'image-size readout for XPan'),
    (0x0893290,
        '80301be50b10c2e5be31c2e10530a0e107c0a0e100e093e5103083e20c0013e5'
        '10c08ce2081013e5042013e5080053e110e00ce50c000ce508100ce504200ce5'
        'f3ffff1a001093e5',
        '100403e3010545e397c200e30c0054e15c0b0a03870345031eff2fe1100403e3'
        '010545e397c200e30c0057e15c0b0a03870345031eff2fe1bcb5875301003c00'
        '2800000074803300',
     'XPan icon'),
    (0x0893310,
        'c4a084e298340ee30160a0e30a40a0e1fc3345e36c300be50490b4e5018056e2'
        '0050a0131470a01310a094e50500a0110610a013c601000a60301be5b211c9e1'
        '5e1da0e3055083e05c301be57550ffe6b401c9e13890a0e3b890cae1032067e0'
        '022065e00a00a0e1ba20cae1fe1f00eb0a00a0e10710a0e1fe1f00eb0a00a0e1'
        '3c10a0e3fe1f00eb0a00a0e10510a0e1fe1f00eb010058e3b801000a040056e3'
        '0100000a016086e2daffffea64401be558a01be5f0c094e50410a0e1c42094e5'
        '0a00a0e1c0809ce500309ae5c8509ce5801092e8103093e55cc00be5086092e5'
        'e89094e533ff2fe13a20a0e31c30a0e3b020c8e1842701e3b230c8e1b83f00e3'
        'b630c8e10410a0e1b420c8e10a00a0e10020a0e38bf6ffebf55501eb000087e5'
        '000050e30020a0e37e3ea0e348200be50080a0e144200be5facea0e33c200be5'
        '020ba0e3b6344be1211da0e3be334be1b4c44be1b0044be1bc134be10b0000da'
        '0210a0e102c087e20a3087e248a04be240e04be2b220ece1011081e2080051e1',
        '050051e30100000a040051e3a2e6ebea0400a0e30cd04be200a89de804370be3'
        '873345e30100d3e70cd04be200a89de8040053e30040a0034985ed0a030053e3'
        '4085edea0440a0e34585edea040053e397220003346be60a030053e32b6be6ea'
        '0030a0e380c601e30c0050e1503800030120a00300c501e30c0050e1c0370003'
        '0120a00380c301e30c0050e1303700030120a00380c001e30c0050e118360003'
        '0220a00300cf00e30c0050e1883500030220a00300cc00e30c0050e170340003'
        '0320a00380ca00e30c0050e1e03300030320a00300c900e30c0050e150330003'
        '0320a003000053e3f2feff0a030054e1f0feff1a0230a0e1e49cecea02030401'
        '0543000001050000581f0055d41f0055ac200055402000551cb787530c000000'
        '30180000f0080000801600005008000000150000c00700008013000030070000'
        '50130000200700008010000018060000000f000088050000b00d000010050000'
        '000c000070040000800a0000e0030000000900005003000080070000c8020000',
     'RAW Development and Crop: XPan'),
    (0x089cfa8, 'da47d1e5', '27d8ffea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x089d0c0, 'da27d8e5', 'd9d7ffea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x089d218, 'da77d1e5', '93d7ffea',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x08a44f4, 'f0c788532cc8885324c88853', '1cc888531cc888531cc88853',
     'live view: whole frame with the crop dimmed'),
    (0x08e7210,
        '6e00008a010055e38100000a000056e38600001a030055e34700000a6c3908e3'
        '201806e3fd3345e3602507e304308be5fd1345e3fd2345e30000a0e37730a0e3'
        '24d04be2f06b9de8f87800ea640053e33000000a7d0053e3a500000ab20053e3'
        '4200000a6c3908e3201806e3fd3345e3',
        '0dc0a0e10020a0e378d82de904b04ce20050a0e10160a0e1043095e5040056e3'
        '01c0a00300c0a013dbc7c3e5040051e30210a0037d41faeb004050e20600000a'
        '0500a0e1040056e30210a0030610a0110120a0e1e85cfaeb0040a0e10500a0e1'
        '0410a0e1f035faeb0400a0e178a89de8',
     'aspect menu: XPan as a fifth ratio'),
    (0x08e7300, '0800001a6c3908e3', '0001030204000000',
     'aspect menu: XPan as a fifth ratio'),
    (0x08e7310,
        '602507e300308de5fd1345e3fd2345e33a30a0e3c57800eb000054e3b8ffff0a'
        '030057e307f19f97470000eaa8f68c5390f68c5378f68c5358f68c53030057e3'
        '07f19f979f0000ea24f88c5314f88c53e4f78c5334f88c531e2da0e3053ca0e3'
        'b020c8e1b030c9e124d04be2f0ab9de8000054e35400000ad22ea0e3233da0e3'
        'b020c8e1b030c9e124d04be2f0ab9de84b2da0e3323da0e3b020c8e1b030c9e1'
        '24d04be2f0ab9de8702701e3fa3ea0e3b020c8e1b030c9e124d04be2f0ab9de8'
        '6c3908e3201806e3fd3345e3602507e300308de5fd1345e3fd2345e34630a0e3'
        '927800eb86ffffea6c3908e3201806e3fd3345e3602507e300308de5fd1345e3'
        'fd2345e30000a0e33d30a0e3877800ebc0ffffea030057e307f19f975d0000ea'
        'b8f78c53a4f78c5390f78c537cf78c53030057e307f19f976e0000ea84f88c53'
        '70f88c5358f88c5344f88c536c3908e3201806e3fd3345e3602507e304308be5'
        'fd1345e3fd2345e30000a0e35330a0e324d04be2f06b9de86c7800ea1e2da0e3'
        '5a3ea0e3b020c8e1b030c9e1b5ffffeabb2ea0e3233da0e3b020c8e1b030c9e1'
        'b0ffffeab02001e3323da0e3b020c8e1b030c9e1abffffead02401e3fa3ea0e3'
        'b020c8e1b030c9e1a6ffffea010055e3eeffff0a000056e31e00001a030055e3'
        '4dffff1a233da0e3b030c8e1b030c9e19cffffea000054e3a4ffff1a010055e3'
        'e7ffff0a000056e31800001a030055e341ffff1a323da0e3b030c8e1b030c9e1'
        '90ffffeafa3ea0e3b030c8e1b030c9e18cffffea053ca0e3b030c8e1b030c9e1'
        '88ffffea1e2da0e3383400e3b020c8e1b030c9e183ffffead22ea0e3763ea0e3'
        'b020c8e1b030c9e17effffea0000c8424b2da0e3a93ea0e3b020c8e1b030c9e1'
        '78ffffea702701e3d33ea0e3b020c8e1b030c9e173ffffea6c3908e3201806e3'
        'fd3345e3602507e3',
        '0000000000000000000000000000000000000000000000000000000000000000'
        '0000000000000000000000000000000000000000000000000000000000000000'
        '00000000000000000000000000000000000000000000000028000000e0010000'
        '10000000a80200000000000028000000e0010000100000002600000000000000'
        '02000000e001000002000000a80200000000000002000000e001000002000000'
        '0000000000000000d0020000260000001000000000000000ba010000d0020000'
        '26000000100000000000000024000000d0020000020000000200000000000000'
        'ba010000d00200000200000002000000000000000000000078000000e0010000'
        '10000000580200000000000078000000e0010000100000007600000000000000'
        '02000000e001000002000000580200000000000002000000e001000002000000'
        '0000000000000000d00200006b000000100000000000000075010000d0020000'
        '6b000000100000000000000069000000d0020000020000000200000000000000'
        '75010000d002000002000000020000000dc0a0e1f0d82de904b04ce218d04de2'
        '0040a0e10150a0e1f430d4e5020053e30900003a0600000a033043e2f430c4e5'
        '20a4f2ebf430d4e5033083e2f430c4e5030000ea35e2f2eb010000ea19a4f2eb'
        '1e0000eaa6bce5eb0abee5ebab25e7eb040050e31900008a00660fe38c6345e3'
        '006286e0006386e00470a0e3083096e5000053e30e00000a00508de5003096e5'
        '04308de5043096e508308de5083096e50c308de50c3096e510308de5103096e5'
        '1430cde5dbb0e5eb38b1e5eb0d10a0e14cb3e5eb146086e2017057e2eaffff1a'
        '1cd04be2f0a89de80dc0a0e118d82de904b04ce20040a0e1d6a3f2ebf430d4e5'
        '033083e2f430c4e514d04be218a89de80600a0e10210a0e31020a0e3cda3f2eb'
        '0150a0e304fee2ea',
     'live view: whole frame with the crop dimmed'),
    (0x0df2894, '50006f006d001b017200200073007400720061006e000000', '5800500061006e0000000000000000000000000000000000',
     'menu label "XPan" (Czech)'),
    (0x0df3c44, '0c010000', '05010000',
     'menu label "XPan" (Czech)'),
    (0x0dfdc74, '0d010000', '05010000',
     'menu label "XPan" (Danish)'),
    (0x0dff418,
        '420069006c006c006500640066006f0072006d006100740000000000',
        '5800500061006e000000000000000000000000000000000000000000',
     'menu label "XPan" (Danish)'),
    (0x0e036bc, '0d010000', '05010000',
     'menu label "XPan" (English)'),
    (0x0e0b5dc,
        '410073007000650063007400200052006100740069006f0000000000',
        '5800500061006e000000000000000000000000000000000000000000',
     'menu label "XPan" (English)'),
    (0x0e0c778, '0a010000', '05010000',
     'menu label "XPan" (Finnish)'),
    (0x0e13e3c, '4b00750076006100730075006800640065000000', '5800500061006e00000000000000000000000000',
     'menu label "XPan" (Finnish)'),
    (0x0e167c0, '11010000', '05010000',
     'menu label "XPan" (French)'),
    (0x0e1e4c0,
        '4c006f006e00670075006500750072002f006c00610072006700650075007200'
        '00000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (French)'),
    (0x0e20400,
        '530065006900740065006e007600650072006800e4006c0074006e0069007300'
        '00000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (German)'),
    (0x0e23fd4, '11010000', '05010000',
     'menu label "XPan" (German)'),
    (0x0e2e2cc, '11010000', '05010000',
     'menu label "XPan" (Greek)'),
    (0x0e3350c,
        '9103bd03b103bb03bf03b303af03b1032000a003bb03b503c503c103ce03bd03'
        '00000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (Greek)'),
    (0x0e39c90, '09010000', '05010000',
     'menu label "XPan" (Hungarian)'),
    (0x0e3d9a4, '4b00e900700061007200e1006e00790000000000', '5800500061006e00000000000000000000000000',
     'menu label "XPan" (Hungarian)'),
    (0x0e44440, '11010000', '05010000',
     'menu label "XPan" (Italian)'),
    (0x0e46fdc,
        '46006f0072006d00610074006f00200069006d006d006100670069006e006500'
        '00000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (Italian)'),
    (0x0e4e79c, 'a230b930da30af30c830d46b00000000', '5800500061006e000000000000000000',
     'menu label "XPan" (Japanese)'),
    (0x0e4e8ec, '07010000', '05010000',
     'menu label "XPan" (Japanese)'),
    (0x0e50dbc, '05010000', '05010000',
     'menu label "XPan" (Korean)'),
    (0x0e547d8, '54d6c1c044be28c700000000', '5800500061006e0000000000',
     'menu label "XPan" (Korean)'),
    (0x0e5b050, '10010000', '05010000',
     'menu label "XPan" (Dutch)'),
    (0x0e5ecb4,
        '4200650065006c00640076006500720068006f007500640069006e0067000000',
        '5800500061006e00000000000000000000000000000000000000000000000000',
     'menu label "XPan" (Dutch)'),
    (0x0e66308, '0a010000', '05010000',
     'menu label "XPan" (Polish)'),
    (0x0e671ec, '500072006f0070006f00720063006a0065000000', '5800500061006e00000000000000000000000000',
     'menu label "XPan" (Polish)'),
    (0x0e6a03c,
        '520065006c006100e700e3006f00200064006500200041007300700065007400'
        '6f000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (Portuguese)'),
    (0x0e6e4fc, '12010000', '05010000',
     'menu label "XPan" (Portuguese)'),
    (0x0e74310, '13010000', '05010000',
     'menu label "XPan" (Russian)'),
    (0x0e79cc8,
        '21043e043e0442043d043e04480435043d04380435042000410442043e044004'
        '3e043d0400000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '0000000000000000',
     'menu label "XPan" (Russian)'),
    (0x0e82014, '04010000cc7de653', '05010000cc38df53',
     'menu label "XPan" (Chinese-S)'),
    (0x0e89bbc, '12010000', '05010000',
     'menu label "XPan" (Spanish)'),
    (0x0e8bf4c,
        '46006f0072006d00610074006f00200064006500200069006d00610067006500'
        '6e000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '00000000',
     'menu label "XPan" (Spanish)'),
    (0x0e911e8,
        '420072006500640064002d006800f6006a0064006600f60072006800e5006c00'
        '6c0061006e00640065000000',
        '5800500061006e00000000000000000000000000000000000000000000000000'
        '000000000000000000000000',
     'menu label "XPan" (Swedish)'),
    (0x0e952a0, '16010000', '05010000',
     'menu label "XPan" (Swedish)'),
    (0x0e9941c, '0d010000', '05010000',
     'menu label "XPan" (Thai)'),
    (0x0e9aab0,
        '2d0e310e150e230e320e2a0e480e270e190e200e320e1e0e00000000',
        '5800500061006e000000000000000000000000000000000000000000',
     'menu label "XPan" (Thai)'),
    (0x0ea3b94, '04010000b49ee853', '05010000cc38df53',
     'menu label "XPan" (Chinese-T)'),
    (0x0ea6fb0, '0e010000', '05010000',
     'menu label "XPan" (Turkish)'),
    (0x0eab400,
        '4700f6007200fc006e007400fc0020004f00720061006e0031010000',
        '5800500061006e000000000000000000000000000000000000000000',
     'menu label "XPan" (Turkish)'),
    (0x0eaea40, '74803300', '14773300',
     'XPan icon'),
    (0x0eb0934, '48885753', '90f78c53',
     'live view: whole frame with the crop dimmed'),
    (0x0ff06b8, 'f8fb8c53', '10b28753',
     'XPan picture: image sizes, RAW crop, previews'),
    (0x0ff06d0, 'b4008d536c018d53', '54b2875370b28753',
     'XPan picture: image sizes, RAW crop, previews'),
]

# The XPan icon (ICONBIN section, 60x40 RGBA), written into space freed by a duplicate icon.
ICON_OFFSET = 0x3b73cc0
ICON_BYTES = 9600
ICON_OLD_SHA256 = '3839b322c6898ec64a94b3929f38a2d0cf10034a6d1118efefb0c83b54b23808'
ICON_NEW = (
    'eNrtms1PWkEQwPtPqRVsaKzgRxOtVUkUtJEqcrEnidZQKzGx8QtfE5tovCH2ZCONJfFMCcbEEqIF'
    'UUjUxHizBzXBD3TaGbsLDyilh5KH7iRz2Jl9L/vbj5lZHgDwAO6pDg8Pw13UXLwlJaV3SgWv4EUt'
    'dhG8+fEW2/4VvIJX8P6Zd2npE9lPTk5Ara7gdp/PR/b9/X0oLS2DlZUvsvhxeXkJkcgO2Gy2ouJt'
    'b+/gvoGB12SrqamFRCJBNkmSyJbOmyojIyNFtZ8jkQj5vF4vtaenJWpfXFyAVquT8R4eHkJfn5XW'
    'dXNzk2zHx8dQVvawaHjHxsbJd3V1RXw7O7vUXl1d5X0Y7/Z2hNuam1v4e5uamouGt7LyCcTj5+Rf'
    'Xnbzvj09lpy8+ByTrq5u2TtbWvTQ3W2ms5FqxxhRX99AqlKpQKfT0bNVVdqCxmePxyM7kyxO5ctr'
    'NveQraHhGYRCIW6/vr6mZ1UqNfktFgv3zc3Nwfn57TzH43Ho7X1VMF4cb6qwOJWLF/c+E6Oxnc5w'
    'LBbLGtPm5+czeG9ubmR9otFowXhxLXFNk3FKm5MX2XB9WG7SaB7T/mfidDqhs9MEW1vfqX10dJTB'
    '63Z/BpPJBOFwmNqYEwpZb7B4e3p6ChUVj7Ly4v7EXI1zkhy3m/o0Nj4Hu93+a0x2Hq8l6b2MJZW3'
    'o+OFLB9kG9//4tXr9bK9NTT0Nitvuvj9flrb1L44V5jX8Yy4XC4+T+m8ra1tZJucnCw478KCS8YR'
    'CASy8uK+xDW02d6AwWDMch+3w9nZWca8KIm3vFxFNQM7nyyWYH7NFa/Sta7uKZ1lFgPW19dhb29P'
    'cbxWq5X7DQYDZ3c6F/6Jd3BwkL/HZHpJtqkph+J4vd6vMpbFxY+/68QftPb58k5MJMedjFeSonhr'
    'a+v43cDhcJAN15hJf/9A3ryjo+/4c1hfYxzb2PimKN6ZmQ88X1RX13D77u5tDb22tpY3b1ubISNO'
    'sfpJCbxYYxwcHJAd77upPpYTcZxY6+bDizo7O0v3DpRgMEg1Cc4lxjEl5aO/KZ5jrPVZHZxLNRoN'
    'nRPxe47gFbyCV3xPEbzi+6/gvYu89+n/KvdBfwLw2Pur'
)

HEADER, MAGIC, FOOTER_MAGIC = 128, b'RICOH\0\0\0', b'\xa5\x5a\x5a\xa5'
MAX_DISTANCE = 0x2000
LITERAL_CHUNK = 0x6000


class Refused(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def word_sum(data):
    if len(data) % 4:
        raise Refused('data is not 4-byte aligned')
    return sum(w for (w,) in struct.iter_unpack('<I', data)) & 0xffffffff


def decode(data, limit=256 * 1024 * 1024):
    if len(data) < 160 or data[:8] != MAGIC:
        raise Refused('not a RICOH firmware container')
    out = bytearray()
    frames = []
    cursor = HEADER
    while True:
        start = cursor
        if cursor + 2 > len(data):
            raise Refused('container: missing frame terminator')
        descriptor = int.from_bytes(data[cursor:cursor + 2], 'big')
        cursor += 2
        if descriptor == 0:
            return bytes(out), frames, cursor
        size = descriptor & 0x7fff
        end = cursor + size
        if not size or end > len(data):
            raise Refused(f'container: invalid frame at {start:#x}')
        output_start = len(out)
        if descriptor & 0x8000:
            out += data[cursor:end]
            cursor = end
        else:
            while cursor < end:
                if cursor + 2 > end:
                    raise Refused(f'container: truncated flags at {cursor:#x}')
                flags = int.from_bytes(data[cursor:cursor + 2], 'big')
                cursor += 2
                for bit in range(15, -1, -1):
                    if cursor == end:
                        break
                    if not flags & (1 << bit):
                        out.append(data[cursor])
                        cursor += 1
                        continue
                    if cursor + 2 > end:
                        raise Refused('container: truncated reference')
                    a, b = data[cursor], data[cursor + 1]
                    cursor += 2
                    distance = ((a >> 3) << 8) | b
                    length = a & 7
                    if length == 7:
                        while True:
                            if cursor >= end:
                                raise Refused('container: truncated length')
                            extension = data[cursor]
                            cursor += 1
                            length += extension
                            if extension != 255:
                                break
                    if distance == 0:
                        break
                    if distance > len(out):
                        raise Refused('container: reference before start of output')
                    count = length + 3
                    if distance >= count:
                        out += out[-distance:len(out) - distance + count]
                    else:
                        pattern = bytes(out[-distance:])
                        out += (pattern * ((count + distance - 1) // distance))[:count]
                if len(out) > limit:
                    raise Refused('container: decoded size limit exceeded')
        frames.append((start, end, output_start, len(out)))


def check_container(data, payload=None, consumed=None):
    if payload is None:
        payload, _, consumed = decode(data)
    if data[-20:-16] != FOOTER_MAGIC:
        raise Refused('container: footer magic missing')
    enc, dec = struct.unpack_from('<II', data, len(data) - 12)
    if enc != consumed - HEADER or dec != len(payload):
        raise Refused('container: size fields do not match the content')
    if word_sum(data) or word_sum(payload):
        raise Refused('container: checksum mismatch')
    return payload


def sections(payload):
    out, pos = [], 0
    while pos + 16 <= len(payload):
        tag = payload[pos:pos + 8].rstrip(b'\0')
        if not tag or not tag.isalnum() or not tag.isupper():
            break
        size = struct.unpack_from('<I', payload, pos + 12)[0]
        if pos + 16 + size > len(payload):
            break
        out.append((tag.decode(), pos + 16, pos + 16 + size))
        pos += 16 + size
    return out


def differences(a, b, block=1 << 16):
    if len(a) != len(b):
        raise Refused('length mismatch')
    out = []
    for pos in range(0, len(a), block):
        x, y = a[pos:pos + block], b[pos:pos + block]
        if x != y:
            out += [pos + i for i in range(len(x)) if x[i] != y[i]]
    return out


def rezero(payload):
    buf = bytearray(payload)
    last = struct.unpack_from('<I', buf, len(buf) - 4)[0]
    struct.pack_into('<I', buf, len(buf) - 4, (last - word_sum(buf)) & 0xffffffff)
    return bytes(buf)


def literal_frames(data):
    out = bytearray()
    for pos in range(0, len(data), LITERAL_CHUNK):
        chunk = data[pos:pos + LITERAL_CHUNK]
        out += struct.pack('>H', 0x8000 | len(chunk)) + chunk
    return bytes(out)


def rebuild(source, frames, consumed, patched, changed):
    body = bytearray()
    reemitted = 0
    for (c0, c1, d0, d1) in frames:
        if any(d0 <= c < d1 or c < d0 < c + MAX_DISTANCE for c in changed):
            body += literal_frames(patched[d0:d1])
            reemitted += 1
        else:
            body += source[c0:c1]
    body += b'\0\0'
    trailer = bytearray(source[consumed:])
    struct.pack_into('<II', trailer, len(trailer) - 12, len(body), len(patched))
    struct.pack_into('<I', trailer, len(trailer) - 4, 0)
    padding = bytes((-HEADER - len(body) - len(trailer)) % 4)
    out = bytearray(source[:HEADER] + body + padding + trailer)
    struct.pack_into('<I', out, len(out) - 4, (-word_sum(out)) & 0xffffffff)
    return bytes(out), reemitted


def patch(source, log=print):
    digest = sha256(source)
    if digest != OFFICIAL_SHA256 or len(source) != OFFICIAL_BYTES:
        if digest == UNLOCKED_SHA256:
            raise Refused('this file already has XPan; use the official RICOH file')
        if digest in OTHER_KNOWN:
            raise Refused(f'this file is {OTHER_KNOWN[digest]}; use the official RICOH file')
        raise Refused('input is not the official RICOH GR IV 1.11 fwdc248b.bin '
                      f'(SHA-256 {digest}, expected {OFFICIAL_SHA256})')
    log('input: official RICOH GR IV 1.11 firmware (SHA-256 verified)')

    log('decoding container ...')
    payload, frames, consumed = decode(source)
    check_container(source, payload, consumed)
    secs = sections(payload)
    rtos = next((s for s in secs if s[0] == 'RTOS'), None)
    iconbin = next((s for s in secs if s[0] == 'ICONBIN'), None)
    if rtos is None or iconbin is None:
        raise Refused('payload: RTOS or ICONBIN section not found')

    buf = bytearray(payload)
    items = CHANGES
    for off, old, new, what in items:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        have = bytes(buf[off:off + len(old)])
        if have != old:
            raise Refused(f'unexpected original bytes at {off:#x}: {have.hex()} (expected {old.hex()})')
        if not (rtos[1] <= off and off + len(new) <= rtos[2]):
            raise Refused(f'change at {off:#x} is outside the RTOS section')
        buf[off:off + len(new)] = new
        log(f'  {off:#09x}  {what}')
    icon = zlib.decompress(base64.b64decode(''.join(ICON_NEW)))
    if len(icon) != ICON_BYTES or not (iconbin[1] <= ICON_OFFSET and ICON_OFFSET + ICON_BYTES <= iconbin[2]):
        raise Refused('icon data is damaged or outside the ICONBIN section')
    if sha256(bytes(buf[ICON_OFFSET:ICON_OFFSET + ICON_BYTES])) != ICON_OLD_SHA256:
        raise Refused(f'unexpected original icon at {ICON_OFFSET:#x}')
    buf[ICON_OFFSET:ICON_OFFSET + ICON_BYTES] = icon
    log(f'  {ICON_OFFSET:#09x}  XPan icon (60x40)')
    patched = rezero(bytes(buf))

    log('rebuilding container ...')
    changed = differences(payload, patched)
    out, reemitted = rebuild(source, frames, consumed, patched, changed)

    log('verifying result ...')
    again, _, used = decode(out)
    if again != patched:
        raise Refused('verification: rebuilt container does not decode to the patched firmware')
    check_container(out, again, used)
    if out[:HEADER] != source[:HEADER]:
        raise Refused('verification: header changed')
    allowed = {i for off, old, _, _ in items for i in range(off, off + len(bytes.fromhex(old)))}
    allowed |= set(range(ICON_OFFSET, ICON_OFFSET + ICON_BYTES))
    allowed |= set(range(len(payload) - 4, len(payload)))
    stray = [i for i in changed if i not in allowed]
    if stray:
        raise Refused(f'verification: unexpected changes at {[hex(i) for i in stray[:8]]}')
    if [s for s in sections(again)] != secs:
        raise Refused('verification: section layout changed')
    if sha256(out) != UNLOCKED_SHA256:
        raise Refused('verification: result differs from the research-verified image '
                      f'(got {sha256(out)}, expected {UNLOCKED_SHA256})')
    log(f'verified: {len(changed)} payload bytes changed, {reemitted} frames re-encoded, '
        f'only RTOS and ICONBIN changed, SHA-256 matches the verified build')
    return out


def write_atomic(data, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'fwdc248b.bin'
    if target.exists():
        raise Refused(f'{target} already exists; choose another output directory or remove it')
    tmp = target.with_name('.fwdc248b.bin.tmp')
    tmp.write_bytes(data)
    if sha256(tmp.read_bytes()) != sha256(data):
        tmp.unlink()
        raise Refused('write verification failed')
    tmp.rename(target)
    return target


def identify(data, log=print):
    digest = sha256(data)
    names = {OFFICIAL_SHA256: 'official RICOH GR IV 1.11 (unmodified)',
             UNLOCKED_SHA256: f'GR4-XPanUnlock {VERSION} (XPan added next to 16:9)', **OTHER_KNOWN}
    log(f'SHA-256  {digest}')
    log(f'bytes    {len(data)}')
    log(f'file     {names.get(digest, "unknown - not produced by this tool and not the official 1.11 file")}')
    try:
        check_container(data)
        log('container: valid (size fields, footer, both checksums)')
    except Refused as exc:
        log(f'container: INVALID - {exc}')
        return 2
    return 0 if digest in names else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog='gr4_xpanunlock.py', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version=VERSION)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('patch', help='make the XPan firmware from the official file')
    p.add_argument('input', type=Path, help='official RICOH fwdc248b.bin (GR IV 1.11)')
    p.add_argument('-o', '--output-dir', type=Path, default=Path('output'),
                   help='directory for the result (default: ./output); the file is named fwdc248b.bin')
    c = sub.add_parser('check', help='identify a fwdc248b.bin and validate its container')
    c.add_argument('input', type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    if sys.version_info < (3, 8):
        print('Python 3.8 or newer is required', file=sys.stderr)
        return 2
    try:
        data = a.input.read_bytes()
        if a.cmd == 'check':
            return identify(data)
        if (a.output_dir / 'fwdc248b.bin').exists():
            raise Refused(f'{a.output_dir / "fwdc248b.bin"} already exists; '
                          'choose another output directory or remove it')
        print(f'GR4-XPanUnlock {VERSION}')
        out = patch(data)
        target = write_atomic(out, a.output_dir)
        print(f'wrote {target}  (SHA-256 {sha256(out)})')
        print('Copy this file to the root of the SD card and run the camera\'s firmware update.')
        return 0
    except Refused as exc:
        print(f'refused: {exc}', file=sys.stderr)
        print('nothing was written.', file=sys.stderr)
        return 1
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())