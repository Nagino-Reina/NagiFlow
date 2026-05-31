/**
 * shell/navigation.ts
 *
 * Core left-nav destinations (docs/12 §4/§5, docs/03 §3.4). `i18nKey` resolves the label;
 * `requiresUser` destinations are visible-but-gated for guests (docs/12 §8 permission
 * gating). Module `nav.item` contributions append to this list in later phases.
 */

export interface NavDestination {
  i18nKey: string
  icon: string
  to: string
  requiresUser: boolean
}

export const NAV_DESTINATIONS: NavDestination[] = [
  { i18nKey: 'nav.chat', icon: 'mdi-chat-outline', to: '/', requiresUser: false },
  { i18nKey: 'nav.characters', icon: 'mdi-account-multiple-outline', to: '/characters', requiresUser: true },
  { i18nKey: 'nav.scripts', icon: 'mdi-script-text-outline', to: '/scripts', requiresUser: true },
  { i18nKey: 'nav.live', icon: 'mdi-broadcast', to: '/live', requiresUser: true },
  { i18nKey: 'nav.dashboard', icon: 'mdi-view-dashboard-outline', to: '/dashboard', requiresUser: true },
  { i18nKey: 'nav.modules', icon: 'mdi-puzzle-outline', to: '/modules', requiresUser: true },
  { i18nKey: 'nav.settings', icon: 'mdi-cog-outline', to: '/settings', requiresUser: true },
]
