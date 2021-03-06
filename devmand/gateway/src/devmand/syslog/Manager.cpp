/*
Copyright 2020 The Magma Authors.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include <devmand/syslog/Manager.h>

#include <future>

#include <folly/Subprocess.h>

namespace devmand {
namespace syslog {

Manager::Manager() : configGenerator(configFile) {}

void Manager::addIdentifier(
    const std::string& identifer,
    const devices::Id& id) {
  identifiers.emplace(identifer, id);
  configGenerator.add(configTemplate, identifer, id);
}

void Manager::removeIdentifier(
    const std::string& identifer,
    const devices::Id& id) {
  auto range = identifiers.equal_range(identifer);
  for (auto it = range.first; it != range.second; ++it) {
    if (it->second == id) {
      identifiers.erase(it);
      // TODO should add back old one perhaps? idk
      configGenerator.remove(configTemplate, identifer, id);
      break;
    }
  }
}

devices::Id Manager::lookup(const std::string& identifer) const {
  auto range = identifiers.equal_range(identifer);
  for (auto it = range.first; it != range.second; ++it) {
    return it->second;
  }
  return "";
}

void Manager::restartTdAgentBitAsync() const {
  // TODO so this isn't great. I'm not sure if we need to prevent concurrent
  // uses. Probably... Also this should use a thread poll that supports futures
  // but this works.
  std::async(std::launch::async, [] {
    folly::Subprocess proc(std::vector<std::string>{
        "/bin/systemctl", "restart", "magma@td-agent-bit.service"});
    proc.waitChecked();
  });
}

} // namespace syslog
} // namespace devmand
