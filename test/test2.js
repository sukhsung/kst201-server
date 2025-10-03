import { KST201Manager } from "../src/KST201Manager.js";
import {sleep} from "../src/util/util.js"

const VID = 0x0403;
const PID = 0xfaf0;
const SERIAL = 26006611;

const dev_info = { VID: VID, PID: PID, SERIAL: SERIAL };

const count_per_um = 2184.56064;

const kst_manager = new KST201Manager();

await kst_manager.connect(dev_info);

console.log("Connected :" + kst_manager.is_connected());

( () => {kst_manager.start_comm();})();

// await sleep(100)
await kst_manager.add_to_requests({cmd:'move_home',data:""})
// await sleep(10000)

// for (let i=0;i<50;i++) {
// await kst_manager.add_to_requests({cmd:'move_absolute',data:Math.round(i*100*count_per_um)})
// await sleep(5000)
// }

// await kst_manager.close();

// await kst_manager.move_home()
// await kst_manager.move_absolute( Math.round(100*count_per_um) )
// await kst_manager.move_absolute( Math.round(1000*count_per_um) )
// await kst_manager.sleep(5000)
// await kst_manager.move_absolute( Math.round(5000*count_per_um) )
