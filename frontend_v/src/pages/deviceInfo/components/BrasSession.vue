<template>

  <Dialog modal v-model:visible="brasSessionsService.dialogVisible" class="w-full h-full">
    <template #header>
      <div class="flex items-center">
        <div class="text-2xl">
          Сессия абонента <span class="font-mono">"{{ brasSessionsService.current?.mac }}"</span>
        </div>
        <div>
          <span v-if="updatingSessions" class="text-muted text-help" style="cursor: progress">Обновляю...</span>
          <span v-else @click="refreshSessions" class="text-muted text-help" style="cursor: pointer">Обновить</span>
        </div>
      </div>
    </template>

    <div>

      <!--СРЕЗАТЬ СЕССИЮ   -->
      <!--        НОЖ-->

      <Button @click="cutSession" class="btn btn-outline-primary">
        <svg v-if="brasSessionsService.cuttingNow" class="pi-spin icon-30">
          <use xlink:href="#blade-handmade"></use>
        </svg>
        <svg v-else class="icon-30" >
          <use xlink:href="#blade-handmade"></use>
        </svg>
        Cut session
      </Button>

    </div>

    <div class="">

      <!--        SESSIONS-->
      <div v-if="sessions" class="overflow-auto">
        <template v-if="sessions.BRAS1">
          <div class="flex justify-center">
            <Button>BRAS1</Button>
          </div>
          <div class="p-4" v-if="sessions.BRAS1.errors.length">
            {{ sessions.BRAS1.errors }}
          </div>
          <div class="p-4 font-mono" v-html="textToHtml(sessions.BRAS1.session)"></div>
        </template>

        <template v-if="sessions.BRAS2">
          <div class="flex justify-center">
            <Button>BRAS1</Button>
          </div>
          <div class="card p-4" v-if="sessions.BRAS2.errors.length">
            {{ sessions.BRAS2.errors }}
          </div>
          <div class="card p-4 font-mono" v-html="textToHtml(sessions.BRAS2.session)"></div>
        </template>
      </div>

      <!--        LOADING SESSIONS-->
      <div v-else class="flex justify-center">
        <ProgressSpinner/>
      </div>

    </div>

  </Dialog>

  <!--   ICON   -->
  <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
    <symbol id="blade-handmade">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512.001 512.001" xml:space="preserve">
      <polygon style="fill:#4EB9FF;"
               points="206.999,341.441 142.29,276.733 88.251,330.773 89.293,394.438 119.489,428.951 "></polygon>
        <polygon style="fill:#9AD7FF;" points="88.251,330.773 22.548,396.476 53.786,494.653 119.489,428.951 "></polygon>
        <path style="fill:#174461;"
              d="M459.688,112.504c24.428-24.428,24.428-64.034,0-88.462c-24.428-24.428-64.034-24.428-88.462,0  l-9.829,9.829l27.85,60.613l60.613,27.85L459.688,112.504z"></path>
        <polygon style="fill:#FF755C;"
                 points="361.397,33.872 114.032,281.237 135.328,348.403 202.493,369.7 449.86,122.334 "></polygon>
        <path style="fill:#9AD7FF;"
              d="M376.288,135.293c7.69-7.69,7.69-20.159,0-27.85s-20.159-7.69-27.85,0l-42.593,42.593l-7.098,25.665  l-25.665,7.099l-91.738,91.738c-7.69,7.69-7.69,20.159,0,27.85s20.159,7.69,27.85,0l91.738-91.738l7.098-25.665l25.665-7.098  L376.288,135.293z"></path>
        <rect x="280.221" y="160.657" transform="matrix(-0.7071 0.7071 -0.7071 -0.7071 645.442 93.347)"
              style="fill:#174461;" width="46.334" height="39.384"></rect>
        <g>
        <path style="fill:#01121C;"
              d="M133.657,442.76l60.275-60.273l10.731,3.414c4.127,1.312,8.641,0.217,11.703-2.847L473.67,125.747   c13.913-13.913,21.575-32.41,21.575-52.086s-7.663-38.173-21.575-52.086S441.26,0,421.584,0c-19.675,0-38.173,7.661-52.086,21.575   l-10.107,10.107c-0.023,0.023-0.046,0.045-0.068,0.068c-0.022,0.023-0.045,0.046-0.067,0.07L112.193,278.88   c-3.062,3.063-4.16,7.577-2.847,11.704l3.414,10.73l-26.75,26.75c-0.117,0.112-0.231,0.226-0.341,0.342l-65.52,65.52   c-3.062,3.063-4.16,7.577-2.847,11.704l31.277,98.299c1.226,3.852,4.372,6.787,8.3,7.744c0.908,0.22,1.827,0.328,2.738,0.328   c3.036,0,5.993-1.194,8.192-3.393l65.502-65.504C133.429,442.991,133.544,442.877,133.657,442.76z M385.88,37.958   c9.537-9.538,22.216-14.79,35.703-14.79c13.487,0,26.166,5.252,35.703,14.79l0,0c9.537,9.536,14.789,22.216,14.789,35.703   s-5.252,26.168-14.789,35.703l-1.983,1.983l-71.408-71.408L385.88,37.958z M367.516,56.322l71.408,71.408L204.968,361.684   l-54.171-17.237l-13.049-41.011c-0.129-1.807-0.678-3.59-1.651-5.188l-2.537-7.972L367.516,56.322z M123.132,389.717   c-1.94-6.098-8.454-9.464-14.551-7.526c-6.097,1.94-9.465,8.455-7.526,14.551l11.069,34.787l-47.24,47.238l-23.369-73.444   l47.24-47.24l1.853,5.827c1.939,6.095,8.453,9.466,14.55,7.526c6.097-1.94,9.466-8.454,7.527-14.551l-5.487-17.246l13.471-13.471   l9.868,31.013c1.14,3.581,3.945,6.387,7.526,7.526l31.013,9.868l-38.509,38.509L123.132,389.717z"></path>
          <path style="fill:#01121C;"
                d="M200.337,326.292c8.383,0,16.265-3.264,22.192-9.193l168.539-168.54   c5.927-5.927,9.193-13.809,9.193-22.191c0-8.383-3.264-16.265-9.192-22.191c-5.927-5.929-13.809-9.194-22.192-9.194   c-8.383,0-16.265,3.264-22.192,9.193l-42.898,42.898c-0.029,0.028-0.059,0.058-0.088,0.087c-0.03,0.029-0.059,0.059-0.088,0.089   l-33.128,33.128c-0.028,0.027-0.056,0.056-0.083,0.082c-0.028,0.028-0.056,0.056-0.083,0.083l-92.17,92.17   c-5.927,5.927-9.193,13.809-9.193,22.192c0,8.382,3.264,16.264,9.192,22.191C184.073,323.027,191.954,326.292,200.337,326.292z    M363.066,120.559C363.068,120.559,363.068,120.559,363.066,120.559c1.552-1.552,3.616-2.407,5.81-2.407   c2.195,0,4.258,0.855,5.81,2.407c1.551,1.552,2.406,3.614,2.406,5.81c0,2.195-0.855,4.257-2.407,5.809l-34.795,34.795l-11.62-11.62   L363.066,120.559z M311.891,171.735l11.62,11.62l-16.918,16.917l-11.62-11.62L311.891,171.735z M194.527,289.098l84.064-84.063   l11.62,11.62l-84.063,84.062c-1.552,1.552-3.615,2.407-5.81,2.407c-2.195,0-4.258-0.855-5.81-2.407   c-1.551-1.552-2.406-3.614-2.406-5.809S192.975,290.65,194.527,289.098z"></path>
      </g>
    </svg>
    </symbol>
  </svg>

</template>

<script lang="ts">
import {defineComponent} from "vue";

import brasSessionsService from "@/services/bras.sessions";
import brasSessions from "@/services/bras.sessions";
import {textToHtml} from "@/formats.ts";

export default defineComponent({
  data() {
    return {
      brasSessionsService: brasSessionsService,
      updatingSessions: false,
    }
  },

  computed: {
    sessions() {
      return brasSessionsService.sessions
    },
  },

  methods: {
    textToHtml,

    cutSession() {
      if (brasSessionsService.cuttingNow.value) return;
      brasSessionsService.cutSession()
    },

    refreshSessions() {
      if (!brasSessionsService.current.value) return;
      this.updatingSessions = true;
      brasSessions.getSessions(
          brasSessionsService.current.value.mac,
          brasSessionsService.current.value.device,
          brasSessionsService.current.value.port
      ).then(() => this.updatingSessions = false)
    },

  }

})
</script>

<style scoped>
.icon-30 {
  border: none;
  border-radius: 0;
  height: 30px;
  width: 30px;
  vertical-align: middle;
}

.icon-100 {
  border: none;
  border-radius: 0;
  height: 100px;
  width: 100px;
}

.text-help {
  border-bottom: solid #d1d1d1 1px;
  border-radius: 0;
  font-size: 0.75rem;
  margin: 10px;
  cursor: default;
}
</style>