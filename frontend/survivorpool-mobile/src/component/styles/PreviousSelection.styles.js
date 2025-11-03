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
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12,
  },
  selectionsList: {
    gap: 12,
  },
  selectionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingBottom: 8,
  },
  selectionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  weekText: {
    fontSize: 14,
    color: '#6b7280',
  },
  teamInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  teamLogo: {
    width: 24,
    height: 24,
    marginRight: 4,
  },
  teamName: {
    fontSize: 14,
    color: '#000',
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