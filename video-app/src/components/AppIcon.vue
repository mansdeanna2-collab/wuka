<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<script>
// Crisp, consistent 24x24 line icons drawn with currentColor so they inherit
// the surrounding text color. Add new glyphs here to reuse across the app.
const ICONS = {
  home: ['M3 10.5 12 3l9 7.5', 'M5 9.5V21h14V9.5', 'M9.5 21v-6h5v6'],
  globe: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z', 'M3 12h18', 'M12 3c2.5 2.4 3.8 5.6 3.8 9s-1.3 6.6-3.8 9c-2.5-2.4-3.8-5.6-3.8-9S9.5 5.4 12 3Z'],
  tv: ['M4 7h16v11H4z', 'M9 3l3 4 3-4'],
  gamepad: ['M7 11h4M9 9v4', 'M15.5 10.5h.01M18 12.5h.01', 'M7.5 7h9a4 4 0 0 1 3.9 3.1l1 4.4A2.6 2.6 0 0 1 18 17.6c-.9 0-1.7-.5-2.1-1.3L15 14.5H9l-.9 1.8A2.4 2.4 0 0 1 6 17.6a2.6 2.6 0 0 1-2.5-3.1l1-4.4A4 4 0 0 1 7.5 7Z'],
  user: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M4.5 20a7.5 7.5 0 0 1 15 0'],
  search: ['M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z', 'm20 20-3.5-3.5'],
  'chevron-right': ['m9 6 6 6-6 6'],
  'arrow-left': ['M19 12H5', 'm12 5-7 7 7 7'],
  settings: ['M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M19.4 13a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.6 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z'],
  history: ['M3 12a9 9 0 1 0 3-6.7L3 8', 'M3 3v5h5', 'M12 7v5l3 2'],
  star: ['m12 3 2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.3 6.8 19l1-5.8L3.6 9.1l5.8-.8L12 3Z'],
  coins: ['M9 8.5a6 3 0 1 0 0-6 6 3 0 0 0 0 6Z', 'M3 5.5v4c0 1.7 2.7 3 6 3s6-1.3 6-3v-4', 'M15 11a6 3 0 1 0 6 3 6 3 0 0 0-6-3Z', 'M9 15.5v3c0 1.7 2.7 3 6 3s6-1.3 6-3v-3'],
  tool: ['M14.7 6.3a4 4 0 0 0-5.2 5.2L3 18l3 3 6.5-6.5a4 4 0 0 0 5.2-5.2l-2.6 2.6-2.3-.3-.3-2.3 2.5-2.6Z'],
  help: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M9.5 9a2.5 2.5 0 1 1 3.4 2.3c-.8.4-1.4 1-1.4 1.9v.3', 'M12 17h.01'],
  trash: ['M4 7h16', 'M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2', 'M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12', 'M10 11v6M14 11v6'],
  refresh: ['M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8', 'M21 3v5h-5', 'M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16', 'M8 16H3v5'],
  alert: ['M10.3 4 3 17a2 2 0 0 0 1.7 3h14.6a2 2 0 0 0 1.7-3L13.7 4a2 2 0 0 0-3.4 0Z', 'M12 9v4', 'M12 17h.01'],
  'play-circle': ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z', 'm10 8.5 6 3.5-6 3.5Z'],
  dashboard: ['M4 4h7v6H4z', 'M13 4h7v4h-7z', 'M13 11h7v9h-7z', 'M4 13h7v7H4z'],
  folder: ['M3 7a2 2 0 0 1 2-2h3.6a2 2 0 0 1 1.4.6l1.2 1.2a2 2 0 0 0 1.4.6H19a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z'],
  film: ['M4 4h16a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z', 'M8 4v16M16 4v16M3 9h5M3 15h5M16 9h5M16 15h5'],
  download: ['M12 3v12', 'm7 11 5 5 5-5', 'M5 20h14'],
  upload: ['M12 21V9', 'm7 13 5-5 5 5', 'M5 4h14'],
  plus: ['M12 5v14M5 12h14'],
  edit: ['M4 20h4L18.5 9.5a2.1 2.1 0 0 0-3-3L5 17v3Z', 'm14 7 3 3'],
  link: ['M9 14a4 4 0 0 0 6 .5l2-2a4 4 0 0 0-5.7-5.7l-1 1', 'M15 10a4 4 0 0 0-6-.5l-2 2A4 4 0 0 0 12.7 17l1-1'],
  tag: ['M3 3h7.6a2 2 0 0 1 1.4.6l8.4 8.4a2 2 0 0 1 0 2.8l-6.6 6.6a2 2 0 0 1-2.8 0L3 13.6A2 2 0 0 1 2.4 12V3Z', 'M7.5 7.5h.01'],
  x: ['M18 6 6 18M6 6l12 12'],
  rocket: ['M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2a2.8 2.8 0 0 0-3-3Z', 'M9 12a13 13 0 0 1 8-8c2.5 0 3 .5 3 3a13 13 0 0 1-8 8', 'M9 12l3 3', 'M15 9h.01'],
  chart: ['M4 20V4', 'M4 20h16', 'M8 20v-6M12 20V8M16 20v-9M20 20v-4'],
  layers: ['m12 3 9 5-9 5-9-5 9-5Z', 'm3 13 9 5 9-5', 'M3 17l9 5 9-5'],
  filter: ['M3 5h18l-7 8v6l-4 2v-8L3 5Z'],
  'chevron-down': ['m6 9 6 6 6-6'],
  check: ['m5 12 5 5L20 7'],
  image: ['M4 4h16a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z', 'M8.5 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z', 'm4 17 5-5 4 4 3-3 4 4'],
  'arrow-up': ['M12 19V5', 'm6 11 6-6 6 6'],
  'arrow-down': ['M12 5v14', 'm6 13 6 6 6-6'],
}

export default {
  name: 'AppIcon',
  props: {
    name: {
      type: String,
      required: true,
    },
    size: {
      type: [Number, String],
      default: 24,
    },
    strokeWidth: {
      type: [Number, String],
      default: 1.8,
    },
  },
  computed: {
    paths() {
      return ICONS[this.name] || []
    },
  },
}
</script>

<style scoped>
.app-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
