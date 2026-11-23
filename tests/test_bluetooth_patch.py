"""Execute the actual patched C++ function against 24 channel combinations."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class BluetoothPatchTests(unittest.TestCase):
 def test_only_aacp_gains_basic_mode_fallback(self):
  compiler=shutil.which('c++')
  self.assertIsNotNone(compiler,'A C++17 compiler is required for host tests')
  with tempfile.TemporaryDirectory() as d:
   work=Path(d);p=work/'system/stack/l2cap/l2c_fcr.cc';p.parent.mkdir(parents=True)
   p.write_text((ROOT/'tests/fixtures/l2c-fcr-mode-original.cc').read_text())
   subprocess.run(['git','init','-q',d],check=True)
   subprocess.run(['git','-C',d,'apply',str(ROOT/'patches/Bluetooth/0001-aacp-basic-mode-fallback.patch')],check=True)
   prefix='''#include <cassert>
#include <cstdint>
#include <cstddef>
namespace test_case {
namespace log { void warn(const char*) {} }
#define CHECK(x) assert(x)
constexpr uint8_t L2CAP_EXTFEA_ENH_RETRANS=8, L2CAP_FCR_ERTM_MODE=3;
struct Lcb { uint8_t peer_ext_fea; };
struct Ertm { uint8_t preferred_mode; };
struct Rcb { uint16_t real_psm; Ertm ertm_info; };
struct tL2C_CCB { Lcb* p_lcb; Rcb* p_rcb; };
'''
   suffix='''}
int main() {
 unsigned count=0;
 for (uint8_t feature : {uint8_t(0),uint8_t(8)})
 for (uint8_t mode : {uint8_t(0),uint8_t(3)})
 for (uint16_t psm : {0x1001,0x11,0x13,0x19,0x27,0x1003}) {
  test_case::Lcb l{feature}; test_case::Rcb r{psm,{mode}};
  test_case::tL2C_CCB c{&l,&r};
  bool expected=feature || mode!=3 || psm==0x1001;
  if (bool(test_case::l2c_fcr_chk_chan_modes(&c))!=expected) return 1;
  if (r.ertm_info.preferred_mode!=(!feature && mode==3 ? 0 : mode)) return 2;
  ++count;
 }
 assert(count==24);
}
'''
   cc=work/'test.cc';cc.write_text('#include <initializer_list>\n'+prefix+p.read_text()+suffix)
   subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror',str(cc),'-o',str(work/'test')],check=True)
   subprocess.run([str(work/'test')],check=True)
   cc.write_text('#include <initializer_list>\n'+prefix+(ROOT/'tests/fixtures/l2c-fcr-mode-original.cc').read_text()+suffix)
   subprocess.run([compiler,'-std=c++17',str(cc),'-o',str(work/'original')],check=True)
   self.assertNotEqual(0,subprocess.run([str(work/'original')]).returncode,'Unpatched source unexpectedly passes the fallback regression')
