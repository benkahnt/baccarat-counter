from pathlib import Path
import subprocess
from test_toolchain import compile_cpp,temporary_directory
root=Path(__file__).resolve().parents[1]
source=(root/'src/main.cpp').read_text(encoding='utf-8')
code=r'''
#include "evolution_start_policy.h"
#include <cassert>
int main(){
 using evolution_start_policy::Budget;
 Budget b;assert(b.Acquire(1000));
 for(unsigned t=1001;t<61000;t+=100)assert(!b.Acquire(t));
 assert(b.attempts==1);assert(b.Acquire(61000));
 assert(!b.Acquire(180999));assert(b.Acquire(181000));
 assert(!b.Acquire(99999999));assert(b.attempts==3);
 b={};b.denied=true;assert(!b.Acquire(1));assert(!b.Acquire(99999999));
 b={};assert(b.Acquire(10));assert(!b.Acquire(9));
 for(unsigned t=1000;t<=61000;t+=10000)b.ObserveHealthy(t);
 assert(b.attempts==0);assert(b.Acquire(61001));
 b.ObserveHealthy(62000);b.ObserveHealthy(120000);assert(b.attempts==1);
 b.denied=true;for(unsigned t=130000;t<300000;t+=10000)b.ObserveHealthy(t);
 assert(!b.Acquire(300001));
}
'''
with temporary_directory() as d:
 p=Path(d)/'retry.cpp';p.write_text(code)
 exe=compile_cpp(p,Path(d)/'retry',[root/'src']);subprocess.run([str(exe)],check=True,timeout=30)
assert 'Target.createTarget' not in source
a=source.index('    void PauseEvolutionAfterFeedLoss(');b=source.index('    void MaybeRecoverExpiredEvolutionFeed()',a)
recovery=source[a:b]
assert 'Target.closeTarget' not in recovery
assert 'Page.reload' not in recovery and 'Page.navigate' not in recovery
assert 'EvolutionPauseCountingForFeedLoss(reason)' in recovery
assert 'static std::atomic<bool> gEvolutionRollingActionEnabled{false}' in source
assert 'gEvolutionRollingActionEnabled.store(true' not in source
assert 'const bool rollingEvolution = false' in source
assert 'EVOLUTION_PLAY_NAVIGATE_REQUEST' in source and 'EVOLUTION_LAUNCH_ERROR' in source
assert 'evolutionPageLaunchBudget_.denied = true' in source
assert 'evolutionReloadBudget_' not in source
pause=source[source.index('    void EvolutionPauseCountingForFeedLoss('):a]
assert 'shoe.strategyRanks.clear' not in pause
assert 'savedShoeBeforeInterruption = shoe' in pause
print('PASS bounded 60/120-second retries, maximum three attempts, explicit launch-error pause, one tab, no timeout closes')
