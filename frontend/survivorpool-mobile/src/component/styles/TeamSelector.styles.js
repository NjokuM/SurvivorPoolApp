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
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  confirmButton: {
    backgroundColor: '#37003c',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  confirmButtonDisabled: {
    backgroundColor: '#ccc',
    opacity: 0.6,
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  teamsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  teamCard: {
    width: '47%', // Roughly 2 columns with gap
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    position: 'relative',
  },
  teamCardSelected: {
    borderColor: '#37003c',
    backgroundColor: '#f9f5ff',
  },
  teamCardDisabled: {
    opacity: 0.5,
    backgroundColor: '#f5f5f5',
  },
  teamLogo: {
    width: 48,
    height: 48,
    marginBottom: 8,
  },
  teamName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    textAlign: 'center',
    marginBottom: 4,
  },
  teamMatch: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  usedBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#37003c',
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  usedBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});