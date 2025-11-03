import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  table: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    overflow: 'hidden',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#f9fafb',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingVertical: 12,
    paddingHorizontal: 12,
  },
  tableHeaderCell: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  playerColumn: {
    flex: 2,
  },
  selectionColumn: {
    flex: 2,
  },
  resultColumn: {
    flex: 1,
    alignItems: 'flex-end',
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingVertical: 12,
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  tableRowInactive: {
    opacity: 0.5,
  },
  tableRowCurrentUser: {
    backgroundColor: '#f1f5f9',
  },
  playerCell: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  currentUserDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#37003c',
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000',
  },
  playerStatus: {
    fontSize: 12,
    color: '#666',
  },
  selectionCell: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  teamLogo: {
    width: 24,
    height: 24,
  },
  teamName: {
    fontSize: 14,
    color: '#000',
  },
  notSelectedText: {
    fontSize: 14,
    color: '#9ca3af',
  },
  resultBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  resultBadgeWin: {
    backgroundColor: '#dcfce7',
  },
  resultBadgeDraw: {
    backgroundColor: '#fef9c3',
  },
  resultBadgeLoss: {
    backgroundColor: '#fee2e2',
  },
  resultBadgePending: {
    backgroundColor: '#e5e7eb',
  },
  resultText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  resultTextWin: {
    color: '#166534',
  },
  resultTextDraw: {
    color: '#854d0e',
  },
  resultTextLoss: {
    color: '#991b1b',
  },
  resultTextPending: {
    color: '#6b7280',
  },
});