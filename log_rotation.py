"""
Log Retention Manager (日志保留管理器)

Manages log file rotation, compression, and deletion based on retention policy.
管理日志文件轮换、压缩和删除，基于保留策略。

Recommended retention policy:
- Hot logs (uncompressed): 30 days for positions, 90 days for trading, 14 days for errors
- Archived logs (compressed): 1 year for positions, 2 years for trading, 90 days for errors
- Total storage: ~34MB for 1 year

推荐的保留策略：
- 热日志（未压缩）：持仓30天，交易90天，错误14天
- 归档日志（压缩）：持仓1年，交易2年，错误90天
- 总存储：约34MB存储1年数据
"""

import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class LogRetentionManager:
    """
    Manages log file rotation, compression, and deletion
    管理日志文件轮换、压缩和删除
    """
    
    RETENTION_CONFIG = {
        'hot_days': {
            'positions.log': 30,    # 30 days uncompressed (~10MB)
            'trading.log': 90,      # 90 days uncompressed (~2.4MB)
            'errors.log': 14,       # 14 days uncompressed (~1.2MB)
        },
        'archive_days': {
            'positions.log': 365,   # 1 year archived (compressed ~24MB)
            'trading.log': 730,     # 2 years archived (~5MB)
            'errors.log': 90,       # 90 days archived (~2MB)
        }
    }
    
    def __init__(self, logs_dir='logs'):
        """
        Initialize log retention manager
        
        Args:
            logs_dir: Path to logs directory
        """
        self.logs_dir = Path(logs_dir)
        self.archive_dir = self.logs_dir / 'archive'
        self.archive_dir.mkdir(exist_ok=True, parents=True)
    
    def rotate_logs(self):
        """
        Daily rotation:
        1. Compress logs older than hot_days
        2. Move to archive directory
        
        每日轮换：
        1. 压缩超过热期限的日志
        2. 移动到归档目录
        """
        print(f"=== Starting Log Rotation at {datetime.now()} ===\n")
        
        for log_file, hot_days in self.RETENTION_CONFIG['hot_days'].items():
            self._rotate_single_log(log_file, hot_days)
        
        print("\n=== Log Rotation Complete ===")
    
    def _rotate_single_log(self, log_file: str, hot_days: int):
        """
        Rotate a single log file
        
        Args:
            log_file: Name of the log file
            hot_days: Number of days to keep uncompressed
        """
        log_path = self.logs_dir / log_file
        if not log_path.exists():
            print(f"[SKIP] {log_file} - File not found")
            return
        
        # Check file age
        file_mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
        file_age = datetime.now() - file_mtime
        file_size_mb = log_path.stat().st_size / 1024 / 1024
        
        print(f"[INFO] {log_file}:")
        print(f"       Age: {file_age.days} days, Size: {file_size_mb:.2f} MB")
        
        # If file is older than hot retention, archive it
        if file_age.days >= hot_days or file_size_mb > 50:  # Also rotate if > 50MB
            # Generate archive filename with date
            date_str = file_mtime.strftime('%Y%m%d_%H%M%S')
            archive_name = f"{log_file}.{date_str}.gz"
            archive_path = self.archive_dir / archive_name
            
            # Compress and save
            try:
                print(f"       Compressing to: {archive_name}")
                with open(log_path, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                compressed_size_mb = archive_path.stat().st_size / 1024 / 1024
                compression_ratio = (1 - compressed_size_mb / file_size_mb) * 100
                
                print(f"       Compressed: {compressed_size_mb:.2f} MB ({compression_ratio:.1f}% reduction)")
                
                # Clear the original log file (don't delete, keep for logging)
                log_path.write_text('')
                print(f"       Original log cleared")
                
            except Exception as e:
                print(f"       ERROR compressing {log_file}: {e}")
        else:
            print(f"       Keeping hot (age < {hot_days} days)")
    
    def cleanup_old_archives(self):
        """
        Delete archived logs older than archive_days
        删除超过归档期限的压缩日志
        """
        print(f"\n=== Cleaning Up Old Archives at {datetime.now()} ===\n")
        
        for log_file, archive_days in self.RETENTION_CONFIG['archive_days'].items():
            pattern = f"{log_file}.*.gz"
            deleted_count = 0
            freed_space = 0
            
            for archive_file in self.archive_dir.glob(pattern):
                file_age = datetime.now() - datetime.fromtimestamp(archive_file.stat().st_mtime)
                
                if file_age.days > archive_days:
                    file_size = archive_file.stat().st_size
                    try:
                        archive_file.unlink()
                        deleted_count += 1
                        freed_space += file_size
                        print(f"[DELETE] {archive_file.name} (age: {file_age.days} days)")
                    except Exception as e:
                        print(f"[ERROR] Could not delete {archive_file.name}: {e}")
            
            if deleted_count > 0:
                print(f"[INFO] Deleted {deleted_count} old {log_file} archives, freed {freed_space / 1024 / 1024:.2f} MB")
            else:
                print(f"[INFO] No old {log_file} archives to delete")
        
        print("\n=== Cleanup Complete ===")
    
    def get_storage_stats(self) -> dict:
        """
        Get current storage usage statistics
        获取当前存储使用统计
        
        Returns:
            Dictionary with storage metrics
        """
        hot_size = 0
        archive_size = 0
        file_counts = {'hot': {}, 'archive': {}}
        
        # Calculate hot logs size
        for log_file in self.RETENTION_CONFIG['hot_days'].keys():
            log_path = self.logs_dir / log_file
            if log_path.exists():
                size = log_path.stat().st_size
                hot_size += size
                file_counts['hot'][log_file] = {
                    'size_mb': size / 1024 / 1024,
                    'age_days': (datetime.now() - datetime.fromtimestamp(log_path.stat().st_mtime)).days
                }
        
        # Calculate archived logs size
        for log_file in self.RETENTION_CONFIG['archive_days'].keys():
            pattern = f"{log_file}.*.gz"
            archives = list(self.archive_dir.glob(pattern))
            total_archive_size = sum(f.stat().st_size for f in archives)
            archive_size += total_archive_size
            
            file_counts['archive'][log_file] = {
                'count': len(archives),
                'total_size_mb': total_archive_size / 1024 / 1024
            }
        
        return {
            'hot_logs_mb': hot_size / 1024 / 1024,
            'archived_logs_mb': archive_size / 1024 / 1024,
            'total_mb': (hot_size + archive_size) / 1024 / 1024,
            'file_details': file_counts
        }
    
    def print_storage_report(self):
        """Print a detailed storage usage report"""
        stats = self.get_storage_stats()
        
        print("\n" + "="*60)
        print("            LOG STORAGE REPORT")
        print("="*60)
        
        print(f"\nHot Logs (Uncompressed):     {stats['hot_logs_mb']:>10.2f} MB")
        for log_file, details in stats['file_details']['hot'].items():
            print(f"  • {log_file:25s} {details['size_mb']:>7.2f} MB  ({details['age_days']} days old)")
        
        print(f"\nArchived Logs (Compressed):  {stats['archived_logs_mb']:>10.2f} MB")
        for log_file, details in stats['file_details']['archive'].items():
            print(f"  • {log_file:25s} {details['count']} files, {details['total_size_mb']:>7.2f} MB")
        
        print(f"\n{'─'*60}")
        print(f"Total Storage Used:          {stats['total_mb']:>10.2f} MB")
        print("="*60)
        
        # Estimated annual storage
        days_covered = max(
            (details['age_days'] for details in stats['file_details']['hot'].values()),
            default=1
        )
        if days_covered > 0:
            daily_rate = stats['hot_logs_mb'] / days_covered
            annual_projection = daily_rate * 365
            print(f"\nProjected Annual Storage:    {annual_projection:>10.2f} MB")
        
        print()


# CLI tool for manual execution
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage log retention and rotation')
    parser.add_argument('--rotate', action='store_true', help='Rotate logs (compress old logs)')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old archives')
    parser.add_argument('--stats', action='store_true', help='Show storage statistics')
    parser.add_argument('--all', action='store_true', help='Run rotation, cleanup, and show stats')
    
    args = parser.parse_args()
    
    manager = LogRetentionManager()
    
    # Default: show stats if no arguments
    if not any([args.rotate, args.cleanup, args.stats, args.all]):
        args.stats = True
    
    if args.all:
        manager.rotate_logs()
        manager.cleanup_old_archives()
        manager.print_storage_report()
    else:
        if args.rotate:
            manager.rotate_logs()
        if args.cleanup:
            manager.cleanup_old_archives()
        if args.stats:
            manager.print_storage_report()

