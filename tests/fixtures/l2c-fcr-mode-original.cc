/******************************************************************************
 *
 *  Copyright 2004-2012 Broadcom Corporation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at:
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 ******************************************************************************/

uint8_t l2c_fcr_chk_chan_modes(tL2C_CCB* p_ccb) {
  CHECK(p_ccb != NULL);

  /* Remove nonbasic options that the peer does not support */
  if (!(p_ccb->p_lcb->peer_ext_fea & L2CAP_EXTFEA_ENH_RETRANS) &&
      p_ccb->p_rcb->ertm_info.preferred_mode == L2CAP_FCR_ERTM_MODE) {
    log::warn("L2CAP - Peer does not support our desired channel types");
    p_ccb->p_rcb->ertm_info.preferred_mode = 0;
    return false;
  }
  return true;
}
